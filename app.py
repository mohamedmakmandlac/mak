
# import os
# import json
# import uuid
# import faiss
# import numpy as np
# from datetime import datetime, timedelta
# from flask import Flask, request, jsonify, render_template, send_file, make_response
# from flask_cors import CORS
# import google.generativeai as genai
# from dotenv import load_dotenv
# import logging
# import csv
# from io import StringIO
# from werkzeug.security import generate_password_hash, check_password_hash
# import jwt
# from functools import wraps

# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # Configuration
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'your-secret-key-here'
# FAISS_INDEX_PATH = "data/faiss_index.index"
# LEADS_FILE = "data/leads.json"
# CHAT_HISTORY_FILE = "data/chat_history.json"
# USERS_FILE = "data/users.json"
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "your-api-key-here"
# EMBEDDING_DIM = 768  # Gemini embedding dimension

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Initialize Gemini
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel('gemini-1.5-flash')

# # Initialize FAISS with ID mapping
# if os.path.exists(FAISS_INDEX_PATH):
#     faiss_index = faiss.read_index(FAISS_INDEX_PATH)
# else:
#     faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(EMBEDDING_DIM))
#     os.makedirs("data", exist_ok=True)
#     faiss.write_index(faiss_index, FAISS_INDEX_PATH)

# # Customer types
# CUSTOMER_TYPES = [
#     "Builder", "Retail Shop", "Bank", "System Integrator", 
#     "Electrical Consultant", "Security Consultant", "Architect", 
#     "Government", "Airport", "Distributor"
# ]

# # Status workflow
# STATUS_FLOW = {
#     "Pending": ["Contacted", "Follow-Up", "Interested", "Cancelled", "Rejected"],
#     "Contacted": ["Follow-Up", "Interested", "Demo Given", "Cancelled", "Rejected"],
#     "Follow-Up": ["Interested", "Demo Given", "Cancelled", "Rejected"],
#     "Interested": ["Demo Given", "In Progress", "On Hold"],
#     "Demo Given": ["In Progress", "Success", "On Hold"],
#     "In Progress": ["Success", "On Hold", "Completed"],
#     "On Hold": ["In Progress", "Cancelled"],
#     "Success": ["Completed"],
#     "Completed": [],
#     "Cancelled": [],
#     "Rejected": []
# }

# # Map UUIDs to integer indices for FAISS
# id_map = {}  # {uuid_str: int_index}
# next_index = 1

# # JWT Authentication Decorator
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         if 'x-access-token' in request.headers:
#             token = request.headers['x-access-token']
        
#         if not token:
#             return jsonify({'message': 'Token is missing!'}), 401
            
#         try:
#             data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
#             current_user = get_user_by_id(data['user_id'])
#         except:
#             return jsonify({'message': 'Token is invalid!'}), 401
            
#         return f(current_user, *args, **kwargs)
#     return decorated

# def admin_required(f):
#     @wraps(f)
#     def decorated(current_user, *args, **kwargs):
#         if not current_user['is_admin']:
#             return jsonify({'message': 'Admin access required!'}), 403
#         return f(current_user, *args, **kwargs)
#     return decorated

# # Helper Functions
# def normalize_lead(lead):
#     """Normalize lead data to ensure consistency."""
#     normalized = lead.copy()
#     if 'name' in normalized and 'client_name' not in normalized:
#         normalized['client_name'] = normalized['name']
#         del normalized['name']
#     if 'company' in normalized and 'company_name' not in normalized:
#         normalized['company_name'] = normalized['company']
#         del normalized['company']
#     if 'project' in normalized and 'project_requirements' not in normalized:
#         normalized['project_requirements'] = normalized['project']
#         del normalized['project']
#     normalized['id'] = str(normalized['id'])
#     if 'status' not in normalized:
#         normalized['status'] = 'Pending'
#     if 'created_at' not in normalized:
#         normalized['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#     if 'last_updated' not in normalized:
#         normalized['last_updated'] = normalized['created_at']
#     if 'customer_type' not in normalized:
#         normalized['customer_type'] = 'Other'
#     if 'assigned_to' not in normalized:
#         normalized['assigned_to'] = None
#     if 'created_by' not in normalized:
#         normalized['created_by'] = None
#     if 'cancel_reason' not in normalized:
#         normalized['cancel_reason'] = None
#     return normalized

# def load_leads():
#     try:
#         with open(LEADS_FILE, 'r') as f:
#             data = json.load(f)
#             return [normalize_lead(lead) for lead in data] if isinstance(data, list) else []
#     except (FileNotFoundError, json.JSONDecodeError):
#         return []

# def save_leads(leads):
#     with open(LEADS_FILE, 'w') as f:
#         json.dump(leads, f, indent=2)

# def load_chat_history():
#     try:
#         with open(CHAT_HISTORY_FILE, 'r') as f:
#             data = json.load(f)
#             return data if isinstance(data, list) else []
#     except (FileNotFoundError, json.JSONDecodeError):
#         return []

# def save_chat_history(history):
#     with open(CHAT_HISTORY_FILE, 'w') as f:
#         json.dump(history, f, indent=2)

# def load_users():
#     try:
#         with open(USERS_FILE, 'r') as f:
#             data = json.load(f)
#             return data if isinstance(data, list) else []
#     except (FileNotFoundError, json.JSONDecodeError):
#         # Create default admin user if no users exist
#         users = [{
#             'id': str(uuid.uuid4()),
#             'username': 'admin',
#             'password': generate_password_hash('admin123'),
#             'name': 'Admin User',
#             'email': 'admin@example.com',
#             'is_admin': True,
#             'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#         }]
#         save_users(users)
#         return users

# def save_users(users):
#     with open(USERS_FILE, 'w') as f:
#         json.dump(users, f, indent=2)

# def get_user_by_id(user_id):
#     users = load_users()
#     return next((user for user in users if user['id'] == user_id), None)

# def get_user_by_username(username):
#     users = load_users()
#     return next((user for user in users if user['username'] == username), None)

# def get_embedding(text):
#     """Generate embedding for text using Gemini."""
#     try:
#         result = genai.embed_content(model="models/embedding-001", content=text)
#         return np.array(result['embedding'], dtype=np.float32)
#     except Exception as e:
#         logger.error(f"Error generating embedding: {e}")
#         return np.zeros(EMBEDDING_DIM, dtype=np.float32)

# def get_faiss_index(lead_id):
#     """Map lead ID to FAISS integer index."""
#     global next_index
#     lead_id_str = str(lead_id)
#     if lead_id_str not in id_map:
#         id_map[lead_id_str] = next_index
#         next_index += 1
#     return id_map[lead_id_str]

# def index_lead(lead, lead_id):
#     """Index lead data in FAISS with embedding."""
#     try:
#         lead = normalize_lead(lead)
#         if not lead.get('client_name'):
#             return
#         lead_text = f"{lead['client_name']} {lead.get('company_name', '')} {lead.get('project_requirements', '')} {lead.get('notes', '')}"
#         embedding = get_embedding(lead_text)
#         faiss_index.add_with_ids(embedding.reshape(1, -1), np.array([get_faiss_index(lead_id)], dtype=np.int64))
#         faiss.write_index(faiss_index, FAISS_INDEX_PATH)
#     except Exception as e:
#         logger.error(f"Error indexing lead {lead_id}: {e}")

# def reindex_all_leads():
#     """Reindex all leads in FAISS."""
#     global faiss_index, id_map, next_index
#     try:
#         faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(EMBEDDING_DIM))
#         id_map = {}
#         next_index = 1
#         leads = load_leads()
#         for lead in leads:
#             lead_id = lead.get('id')
#             if lead_id:
#                 index_lead(lead, lead_id)
#     except Exception as e:
#         logger.error(f"Error reindexing leads: {e}")

# def get_upcoming_reminders(user_id=None):
#     leads = load_leads()
#     today = datetime.now().date()
#     tomorrow = today + timedelta(days=1)
#     week_later = today + timedelta(days=7)
    
#     reminders = []
    
#     for lead in leads:
#         # Filter by user if specified
#         if user_id and lead.get('assigned_to') != user_id and lead.get('created_by') != user_id:
#             continue
            
#         # Meetings today/tomorrow
#         if lead.get('meeting_date'):
#             try:
#                 meeting_date = datetime.strptime(lead['meeting_date'], "%Y-%m-%d").date()
#                 if meeting_date == today:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     reminders.append({
#                         'type': 'meeting',
#                         'message': f"Meeting with {lead['client_name']} today at {lead.get('meeting_time', '')}{assigned_text}",
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'time': lead.get('meeting_time', ''),
#                         'date': lead['meeting_date']
#                     })
#                 elif meeting_date == tomorrow:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     reminders.append({
#                         'type': 'meeting',
#                         'message': f"Meeting with {lead['client_name']} tomorrow at {lead.get('meeting_time', '')}{assigned_text}",
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'time': lead.get('meeting_time', ''),
#                         'date': lead['meeting_date']
#                     })
#                 elif today < meeting_date <= week_later:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     reminders.append({
#                         'type': 'meeting',
#                         'message': f"Meeting with {lead['client_name']} on {lead['meeting_date']} at {lead.get('meeting_time', '')}{assigned_text}",
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'time': lead.get('meeting_time', ''),
#                         'date': lead['meeting_date']
#                     })
#             except ValueError:
#                 continue
        
#         # Pending review
#         if lead.get('status') in ['Pending', 'Follow-Up']:
#             try:
#                 last_updated = datetime.strptime(lead['last_updated'], "%Y-%m-%d %H:%M:%S.%f").date()
#                 days_since_update = (today - last_updated).days
#                 if days_since_update >= 5:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     reminders.append({
#                         'type': 'review',
#                         'message': f"Follow up with {lead['client_name']} (Pending for {days_since_update} days){assigned_text}",
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'days_pending': days_since_update
#                     })
#             except ValueError:
#                 continue
    
#     return reminders

# def format_lead_details(lead):
#     """Format lead details for display."""
#     lead = normalize_lead(lead)
#     created_by = get_user_by_id(lead.get('created_by')) if lead.get('created_by') else None
#     assigned_to = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
    
#     return {
#         'id': lead['id'],
#         'client_name': lead['client_name'],
#         'company_name': lead.get('company_name', 'N/A'),
#         'email': lead.get('email', 'N/A'),
#         'phone': lead.get('phone', 'N/A'),
#         'project_requirements': lead.get('project_requirements', 'N/A'),
#         'status': lead['status'],
#         'probability': lead.get('probability', 'N/A'),
#         'meeting_date': lead.get('meeting_date', 'N/A'),
#         'meeting_time': lead.get('meeting_time', ''),
#         'notes': lead.get('notes', 'N/A'),
#         'created_at': lead['created_at'],
#         'last_updated': lead['last_updated'],
#         'customer_type': lead.get('customer_type', 'Other'),
#         'created_by': created_by['name'] if created_by else 'N/A',
#         'created_by_id': lead.get('created_by'),
#         'assigned_to': assigned_to['name'] if assigned_to else 'N/A',
#         'assigned_to_id': lead.get('assigned_to'),
#         'cancel_reason': lead.get('cancel_reason', 'N/A')
#     }

# def generate_gemini_response(query, leads):
#     """Generate response using Gemini with lead context."""
#     try:
#         # Format leads for context
#         leads_context = "\n".join([
#             f"Lead ID: {lead['id']}, Client: {lead['client_name']}, Company: {lead.get('company_name', 'N/A')}, "
#             f"Status: {lead['status']}, Probability: {lead.get('probability', 'N/A')}%, "
#             f"Meeting: {lead.get('meeting_date', 'N/A')} at {lead.get('meeting_time', 'N/A')}, "
#             f"Project: {lead.get('project_requirements', 'N/A')}, Notes: {lead.get('notes', 'N/A')}"
#             for lead in leads
#         ])
        
#         # Generate prompt
#         prompt = f"""
#         You are an AI lead management assistant. Based on the following query and lead data, provide a concise and accurate response.
        
#         Query: {query}
        
#         Lead Data:
#         {leads_context}
        
#         Instructions:
#         1. For listing requests, show relevant leads with key details
#         2. For filtering requests, apply the filter and show results
#         3. For status changes, verify the transition is valid
#         4. For meeting scheduling, confirm details are complete
#         5. Always be concise and factual
#         6. Include reminders if any are upcoming
        
#         Current Date: {datetime.now().strftime("%Y-%m-%d")}
#         """
        
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         logger.error(f"Error generating Gemini response: {e}")
#         return "Sorry, I couldn't generate a response due to an error."

# def execute_operation(query, user_id=None):
#     """Execute operation using Gemini's understanding."""
#     leads = load_leads()
    
#     # Filter leads by user if not admin
#     if user_id:
#         users = load_users()
#         current_user = next((u for u in users if u['id'] == user_id), None)
#         if not current_user.get('is_admin'):
#             leads = [lead for lead in leads if lead.get('created_by') == user_id or lead.get('assigned_to') == user_id]
    
#     reminders = get_upcoming_reminders(user_id)
    
#     # First get Gemini's response
#     initial_response = generate_gemini_response(query, leads)
    
#     # Check if response indicates an action needs to be taken
#     if any(keyword in initial_response.lower() for keyword in ["update", "change", "schedule", "create", "delete"]):
#         # Get confirmation from Gemini on the action
#         confirmation_prompt = f"""
#         Based on this response to the query "{query}":
#         {initial_response}
        
#         Should any data be updated in the lead management system? 
#         If yes, provide the exact changes in JSON format with:
#         - operation: "create"/"update"/"delete"
#         - lead_id: (if applicable)
#         - field: (if updating)
#         - new_value: (if updating)
#         - new_lead_data: (if creating)
#         """
        
#         try:
#             confirmation = model.generate_content(confirmation_prompt)
#             if "{" in confirmation.text and "}" in confirmation.text:
#                 # Extract JSON from response
#                 start = confirmation.text.index("{")
#                 end = confirmation.text.rindex("}") + 1
#                 action = json.loads(confirmation.text[start:end])
                
#                 # Execute the action
#                 if action.get("operation") == "update":
#                     leads = load_leads()
#                     lead = next((l for l in leads if str(l['id']) == action.get("lead_id")), None)
#                     if lead:
#                         lead[action.get("field")] = action.get("new_value")
#                         lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#                         save_leads(leads)
#                         index_lead(lead, lead['id'])
                
#                 elif action.get("operation") == "create":
#                     new_lead = action.get("new_lead_data", {})
#                     new_lead['id'] = str(uuid.uuid4())
#                     new_lead['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#                     new_lead['last_updated'] = new_lead['created_at']
#                     leads.append(new_lead)
#                     save_leads(leads)
#                     index_lead(new_lead, new_lead['id'])
                
#                 elif action.get("operation") == "delete":
#                     leads = [l for l in leads if str(l['id']) != action.get("lead_id")]
#                     save_leads(leads)
#                     faiss_index.remove_ids(np.array([get_faiss_index(action.get("lead_id"))], dtype=np.int64))
        
#         except Exception as e:
#             logger.error(f"Error executing action: {e}")
    
#     # Add reminders to response if any
#     if reminders:
#         initial_response += "\n\nReminders:\n" + "\n".join([r['message'] for r in reminders])
    
#     return initial_response

# # Authentication Routes
# @app.route('/api/login', methods=['POST'])
# def login():
#     auth = request.json
    
#     if not auth or not auth.get('username') or not auth.get('password'):
#         return jsonify({'message': 'Could not verify', 'error': 'Login required!'}), 401
    
#     user = get_user_by_username(auth['username'])
    
#     if not user:
#         return jsonify({'message': 'Could not verify', 'error': 'User not found!'}), 401
    
#     if check_password_hash(user['password'], auth['password']):
#         token = jwt.encode({
#             'user_id': user['id'],
#             'exp': datetime.utcnow() + timedelta(hours=24)
#         }, app.config['SECRET_KEY'])
        
#         return jsonify({
#             'token': token,
#             'user': {
#                 'id': user['id'],
#                 'username': user['username'],
#                 'name': user.get('name', ''),
#                 'email': user.get('email', ''),
#                 'is_admin': user.get('is_admin', False)
#             }
#         })
    
#     return jsonify({'message': 'Could not verify', 'error': 'Wrong password!'}), 401

# @app.route('/api/users', methods=['POST'])
# @token_required
# @admin_required
# def create_user(current_user):
#     data = request.json
    
#     if not data.get('username') or not data.get('password'):
#         return jsonify({'message': 'Username and password are required!'}), 400
    
#     if get_user_by_username(data['username']):
#         return jsonify({'message': 'User already exists!'}), 400
    
#     hashed_password = generate_password_hash(data['password'])
    
#     new_user = {
#         'id': str(uuid.uuid4()),
#         'username': data['username'],
#         'password': hashed_password,
#         'name': data.get('name', ''),
#         'email': data.get('email', ''),
#         'is_admin': data.get('is_admin', False),
#         'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#     }
    
#     users = load_users()
#     users.append(new_user)
#     save_users(users)
    
#     return jsonify({
#         'message': 'User created successfully!',
#         'user': {
#             'id': new_user['id'],
#             'username': new_user['username'],
#             'name': new_user['name'],
#             'email': new_user['email'],
#             'is_admin': new_user['is_admin']
#         }
#     })

# # Lead Management Routes
# @app.route('/')
# def home():
#     try:
#         os.makedirs("data", exist_ok=True)
#         if not os.path.exists(LEADS_FILE):
#             with open(LEADS_FILE, 'w') as f:
#                 json.dump([], f)
#         if not os.path.exists(CHAT_HISTORY_FILE):
#             with open(CHAT_HISTORY_FILE, 'w') as f:
#                 json.dump([], f)
#         if not os.path.exists(USERS_FILE):
#             load_users()  # This will create default admin user
#         reindex_all_leads()
#         return '<h1>backend working</h1>';
#     except Exception as e:
#         logger.error(f"Error initializing home route: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/chat', methods=['POST'])
# @token_required
# def chat(current_user):
#     data = request.json
#     user_message = data.get('message', '').strip()
    
#     if not user_message:
#         return jsonify({'error': 'Empty message'}), 400
    
#     chat_history = load_chat_history()
    
#     try:
#         # Handle status change commands directly
#         if any(cmd in user_message.lower() for cmd in ["change status", "update status", "mark as", "move to"]):
#             leads = load_leads()
#             client_name = None
#             new_status = None
            
#             # Extract client name and new status from message
#             parts = user_message.lower().split()
#             for i, part in enumerate(parts):
#                 if part in ["to", "as"] and i < len(parts)-1:
#                     new_status = parts[i+1].capitalize()
#                 elif part not in ["change", "status", "update", "mark", "move"]:
#                     if not client_name:
#                         client_name = part.capitalize()
            
#             # Find the lead
#             lead = next((l for l in leads if l['client_name'].lower().startswith(client_name.lower())), None)
            
#             if not lead:
#                 return jsonify({'response': f"No lead found for client {client_name}"})
            
#             # Validate status transition
#             current_status = lead['status']
#             if new_status not in STATUS_FLOW.get(current_status, []):
#                 return jsonify({'response': f"Cannot change status from {current_status} to {new_status}"})
            
#             # Update status
#             lead['status'] = new_status
#             lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#             save_leads(leads)
            
#             response = f"Lead {lead['id']} ({lead['client_name']}) status changed from {current_status} to {new_status}"
#             reminders = get_upcoming_reminders(current_user['id'])
#             if reminders:
#                 response += "\n\nReminders:\n" + "\n".join([r['message'] for r in reminders])
            
#             chat_history.append({
#                 'user': user_message,
#                 'bot': response,
#                 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#             })
#             save_chat_history(chat_history)
            
#             return jsonify({'response': response})
        
#         # Handle list commands
#         elif "list all" in user_message.lower() or "show all" in user_message.lower():
#             status = None
#             if "pending" in user_message.lower():
#                 status = "Pending"
#             elif "contacted" in user_message.lower():
#                 status = "Contacted"
#             elif "follow-up" in user_message.lower():
#                 status = "Follow-Up"
#             elif "interested" in user_message.lower():
#                 status = "Interested"
            
#             leads = load_leads()
#             # Filter by user if not admin
#             if not current_user.get('is_admin'):
#                 leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
            
#             if status:
#                 filtered_leads = [l for l in leads if l['status'] == status]
#             else:
#                 filtered_leads = leads
            
#             response = f"{status if status else 'All'} Leads:\n\n" if filtered_leads else "No leads found\n"
#             for lead in filtered_leads:
#                 response += f"* **Lead ID:** {lead['id']}, **Client:** {lead['client_name']}, **Company:** {lead.get('company_name', 'N/A')}, "
#                 response += f"**Status:** {lead['status']}, **Probability:** {lead.get('probability', 'N/A')}%, "
#                 meeting_info = f"{lead.get('meeting_date', 'N/A')} at {lead.get('meeting_time', 'N/A')}" if lead.get('meeting_date') else "None"
#                 response += f"**Meeting:** {meeting_info}\n"
            
#             reminders = get_upcoming_reminders(current_user['id'])
#             if reminders:
#                 response += "\nReminders:\n" + "\n".join([r['message'] for r in reminders])
            
#             chat_history.append({
#                 'user': user_message,
#                 'bot': response,
#                 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#             })
#             save_chat_history(chat_history)
            
#             return jsonify({'response': response})
        
#         # Handle show lead command
#         elif user_message.lower().startswith('show lead'):
#             lead_name = user_message[10:].strip()
#             leads = load_leads()
#             # Filter by user if not admin
#             if not current_user.get('is_admin'):
#                 leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
            
#             matching_leads = [l for l in leads if lead_name.lower() in l['client_name'].lower()]
            
#             if not matching_leads:
#                 response = f"No leads found matching '{lead_name}'"
#             elif len(matching_leads) == 1:
#                 response = format_lead_details(matching_leads[0])
#             else:
#                 response = f"Multiple leads found matching '{lead_name}':\n"
#                 for lead in matching_leads:
#                     response += f"- {lead['client_name']} (ID: {lead['id']}, Status: {lead['status']})\n"
#                 response += "\nPlease specify which lead you want to see."
            
#             chat_history.append({
#                 'user': user_message,
#                 'bot': response,
#                 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#             })
#             save_chat_history(chat_history)
            
#             return jsonify({'response': response})
        
#         # Handle add notes command
#         elif "add notes" in user_message.lower() or "update notes" in user_message.lower():
#             parts = user_message.split()
#             lead_name = None
#             notes_start = None
            
#             # Find where the notes start
#             for i, part in enumerate(parts):
#                 if part.lower() in ["notes", "note"] and i < len(parts)-1:
#                     notes_start = i+1
#                     break
            
#             # Find lead name before "notes"
#             for i, part in enumerate(parts):
#                 if part.lower() in ["notes", "note"]:
#                     lead_name = " ".join(parts[:i])
#                     break
            
#             if not lead_name or not notes_start:
#                 response = "Please specify both the lead name and the notes to add."
#             else:
#                 leads = load_leads()
#                 # Filter by user if not admin
#                 if not current_user.get('is_admin'):
#                     leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
                
#                 lead = next((l for l in leads if lead_name.lower() in l['client_name'].lower()), None)
                
#                 if not lead:
#                     response = f"No lead found matching '{lead_name}'"
#                 else:
#                     notes = " ".join(parts[notes_start:])
#                     lead['notes'] = notes
#                     lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#                     save_leads(leads)
#                     index_lead(lead, lead['id'])
#                     response = f"Notes updated for {lead['client_name']} (ID: {lead['id']})"
            
#             chat_history.append({
#                 'user': user_message,
#                 'bot': response,
#                 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#             })
#             save_chat_history(chat_history)
            
#             return jsonify({'response': response})
        
#         # Default to Gemini for other queries
#         else:
#             response = execute_operation(user_message, current_user['id'])
            
#             chat_history.append({
#                 'user': user_message,
#                 'bot': response,
#                 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#             })
#             save_chat_history(chat_history)
            
#             return jsonify({'response': response})
    
#     except Exception as e:
#         logger.error(f"Error processing chat message: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/leads', methods=['GET'])
# @token_required
# def get_all_leads(current_user):
#     leads = load_leads()
    
#     # Filter by user if not admin
#     if not current_user.get('is_admin'):
#         leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
    
#     return jsonify([format_lead_details(lead) for lead in leads])

# @app.route('/api/leads/<lead_id>', methods=['GET'])
# @token_required
# def get_lead(current_user, lead_id):
#     leads = load_leads()
#     lead = next((l for l in leads if str(l['id']) == lead_id), None)
    
#     if not lead:
#         return jsonify({'error': 'Lead not found'}), 404
    
#     # Check permission if not admin
#     if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
#         return jsonify({'error': 'Unauthorized access'}), 403
    
#     return jsonify(format_lead_details(lead))

# @app.route('/api/leads', methods=['POST'])
# @token_required
# def create_lead(current_user):
#     try:
#         data = request.json
#         if not data.get('client_name'):
#             return jsonify({'error': 'Client name is required'}), 400
            
#         lead_id = str(uuid.uuid4())
#         new_lead = {
#             'id': lead_id,
#             'client_name': data.get('client_name'),
#             'company_name': data.get('company_name'),
#             'email': data.get('email'),
#             'phone': data.get('phone'),
#             'project_requirements': data.get('project_requirements'),
#             'status': data.get('status', 'Pending'),
#             'probability': data.get('probability', 50),
#             'meeting_date': data.get('meeting_date'),
#             'meeting_time': data.get('meeting_time'),
#             'notes': data.get('notes'),
#             'customer_type': data.get('customer_type', 'Other'),
#             'created_by': current_user['id'],
#             'assigned_to': data.get('assigned_to'),
#             'cancel_reason': data.get('cancel_reason'),
#             'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
#             'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#         }
        
#         leads = load_leads()
#         leads.append(new_lead)
#         save_leads(leads)
#         index_lead(new_lead, lead_id)
        
#         return jsonify({
#             'success': True,
#             'message': f"Lead created for {new_lead['client_name']}",
#             'lead': format_lead_details(new_lead)
#         })
        
#     except Exception as e:
#         logger.error(f"Error creating lead: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/leads/<lead_id>', methods=['PUT'])
# @token_required
# def update_lead(current_user, lead_id):
#     try:
#         data = request.json
#         leads = load_leads()
#         lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
#         if lead_index is None:
#             return jsonify({'error': 'Lead not found'}), 404
            
#         lead = leads[lead_index]
        
#         # Check permission if not admin
#         if not current_user.get('is_admin') and lead.get('created_by') != current_user['id']:
#             return jsonify({'error': 'Unauthorized to update this lead'}), 403
        
#         # Update status if provided and valid
#         if 'status' in data:
#             current_status = lead['status']
#             if data['status'] in STATUS_FLOW.get(current_status, []):
#                 lead['status'] = data['status']
#             else:
#                 return jsonify({'error': f'Invalid status transition from {current_status} to {data["status"]}'}), 400
        
#         # Update other fields
#         for field in ['client_name', 'company_name', 'email', 'phone', 'project_requirements',
#                      'meeting_date', 'meeting_time', 'probability', 'notes', 'customer_type',
#                      'assigned_to', 'cancel_reason']:
#             if field in data:
#                 lead[field] = data[field]
        
#         lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#         leads[lead_index] = lead
#         save_leads(leads)
        
#         # Reindex lead in FAISS
#         faiss_index.remove_ids(np.array([get_faiss_index(lead_id)], dtype=np.int64))
#         index_lead(lead, lead_id)
        
#         return jsonify({
#             'success': True,
#             'message': f"Lead updated for {lead['client_name']}",
#             'lead': format_lead_details(lead)
#         })
        
#     except Exception as e:
#         logger.error(f"Error updating lead {lead_id}: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/leads/<lead_id>', methods=['DELETE'])
# @token_required
# def delete_lead(current_user, lead_id):
#     try:
#         leads = load_leads()
#         lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
#         if lead_index is None:
#             return jsonify({'error': 'Lead not found'}), 404
            
#         lead = leads[lead_index]
        
#         # Check permission if not admin
#         if not current_user.get('is_admin') and lead.get('created_by') != current_user['id']:
#             return jsonify({'error': 'Unauthorized to delete this lead'}), 403
            
#         faiss_index.remove_ids(np.array([get_faiss_index(lead_id)], dtype=np.int64))
#         deleted_lead = leads.pop(lead_index)
#         save_leads(leads)
        
#         return jsonify({
#             'success': True,
#             'message': f"Lead deleted for {deleted_lead['client_name']}"
#         })
        
#     except Exception as e:
#         logger.error(f"Error deleting lead {lead_id}: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/leads/<lead_id>/status', methods=['PUT'])
# @token_required
# def update_lead_status(current_user, lead_id):
#     try:
#         data = request.json
#         if not data.get('status'):
#             return jsonify({'error': 'Status is required'}), 400
            
#         leads = load_leads()
#         lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
#         if lead_index is None:
#             return jsonify({'error': 'Lead not found'}), 404
            
#         lead = leads[lead_index]
        
#         # Check permission if not admin
#         if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
#             return jsonify({'error': 'Unauthorized to update this lead'}), 403
            
#         current_status = lead['status']
#         new_status = data['status']
        
#         if new_status not in STATUS_FLOW.get(current_status, []):
#             return jsonify({'error': f'Invalid status transition from {current_status} to {new_status}'}), 400
        
#         lead['status'] = new_status
#         lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#         leads[lead_index] = lead
#         save_leads(leads)
        
#         # Reindex lead in FAISS
#         faiss_index.remove_ids(np.array([get_faiss_index(lead_id)], dtype=np.int64))
#         index_lead(lead, lead_id)
        
#         return jsonify({
#             'success': True,
#             'message': f"Status updated to {new_status} for {lead['client_name']}",
#             'lead': format_lead_details(lead)
#         })
        
#     except Exception as e:
#         logger.error(f"Error updating status for lead {lead_id}: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/leads/<lead_id>/reminder', methods=['POST'])
# @token_required
# def add_reminder(current_user, lead_id):
#     try:
#         data = request.json
#         if not data.get('date') or not data.get('time'):
#             return jsonify({'error': 'Date and time are required'}), 400
            
#         leads = load_leads()
#         lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
#         if lead_index is None:
#             return jsonify({'error': 'Lead not found'}), 404
            
#         lead = leads[lead_index]
        
#         # Check permission if not admin
#         if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
#             return jsonify({'error': 'Unauthorized to set reminder for this lead'}), 403
            
#         if 'reminders' not in lead:
#             lead['reminders'] = []
            
#         reminder = {
#             'date': data['date'],
#             'time': data['time'],
#             'note': data.get('note', ''),
#             'created_by': current_user['id'],
#             'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#         }
        
#         lead['reminders'].append(reminder)
#         lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#         leads[lead_index] = lead
#         save_leads(leads)
        
#         return jsonify({
#             'success': True,
#             'message': f"Reminder added for {lead['client_name']}",
#             'reminder': reminder
#         })
        
#     except Exception as e:
#         logger.error(f"Error adding reminder for lead {lead_id}: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/leads/export', methods=['POST'])
# @token_required
# def export_leads(current_user):
#     data = request.json
#     leads = load_leads()
    
#     # Filter by user if not admin
#     if not current_user.get('is_admin'):
#         leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
    
#     # Filter leads if parameters provided
#     if data.get('lead_id'):
#         leads = [lead for lead in leads if str(lead['id']) == data['lead_id']]
#     elif data.get('status'):
#         leads = [lead for lead in leads if lead['status'] == data['status']]
#     elif data.get('customer_type'):
#         leads = [lead for lead in leads if lead.get('customer_type') == data['customer_type']]
    
#     if not leads:
#         return jsonify({'error': 'No leads found'}), 404
    
#     # Create a StringIO object for CSV
#     si = StringIO()
#     writer = csv.writer(si)
    
#     # Write header
#     writer.writerow([
#         'ID', 'Client Name', 'Company Name', 'Email', 'Phone', 
#         'Project Requirements', 'Status', 'Probability', 'Customer Type',
#         'Meeting Date', 'Meeting Time', 'Notes', 'Created By', 'Assigned To',
#         'Cancel Reason', 'Created At', 'Last Updated'
#     ])
    
#     # Write data
#     for lead in leads:
#         created_by = get_user_by_id(lead.get('created_by')) if lead.get('created_by') else None
#         assigned_to = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
        
#         writer.writerow([
#             lead['id'],
#             lead['client_name'],
#             lead.get('company_name', ''),
#             lead.get('email', ''),
#             lead.get('phone', ''),
#             lead.get('project_requirements', ''),
#             lead['status'],
#             lead.get('probability', ''),
#             lead.get('customer_type', ''),
#             lead.get('meeting_date', ''),
#             lead.get('meeting_time', ''),
#             lead.get('notes', ''),
#             created_by['name'] if created_by else '',
#             assigned_to['name'] if assigned_to else '',
#             lead.get('cancel_reason', ''),
#             lead['created_at'],
#             lead['last_updated']
#         ])
    
#     # Prepare response
#     output = make_response(si.getvalue())
#     output.headers["Content-Disposition"] = f"attachment; filename=leads_export_{datetime.now().strftime('%Y%m%d')}.csv"
#     output.headers["Content-type"] = "text/csv"
#     return output

# @app.route('/api/notifications', methods=['GET'])
# @token_required
# def get_notifications(current_user):
#     leads = load_leads()
#     today = datetime.now().date()
#     tomorrow = today + timedelta(days=1)
#     week_later = today + timedelta(days=7)
    
#     notifications = {
#         'today': [],
#         'tomorrow': [],
#         'upcoming': [],
#         'pending_review': []
#     }
    
#     for lead in leads:
#         # Filter by user if not admin
#         if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
#             continue
            
#         # Meetings today/tomorrow
#         if lead.get('meeting_date'):
#             try:
#                 meeting_date = datetime.strptime(lead['meeting_date'], "%Y-%m-%d").date()
#                 if meeting_date == today:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     notifications['today'].append({
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'time': lead.get('meeting_time', ''),
#                         'type': 'meeting',
#                         'assigned_to': lead.get('assigned_to'),
#                         'assigned_text': assigned_text
#                     })
#                 elif meeting_date == tomorrow:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     notifications['tomorrow'].append({
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'time': lead.get('meeting_time', ''),
#                         'type': 'meeting',
#                         'assigned_to': lead.get('assigned_to'),
#                         'assigned_text': assigned_text
#                     })
#                 elif today < meeting_date <= week_later:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     notifications['upcoming'].append({
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'date': lead['meeting_date'],
#                         'time': lead.get('meeting_time', ''),
#                         'type': 'meeting',
#                         'assigned_to': lead.get('assigned_to'),
#                         'assigned_text': assigned_text
#                     })
#             except ValueError:
#                 continue
        
#         # Pending review
#         if lead['status'] == 'Pending':
#             try:
#                 created_date = datetime.strptime(lead['created_at'], "%Y-%m-%d %H:%M:%S.%f").date()
#                 days_pending = (today - created_date).days
#                 if days_pending >= 5:
#                     assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
#                     assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
#                     notifications['pending_review'].append({
#                         'lead_id': lead['id'],
#                         'client_name': lead['client_name'],
#                         'days_pending': days_pending,
#                         'type': 'review',
#                         'assigned_to': lead.get('assigned_to'),
#                         'assigned_text': assigned_text
#                     })
#             except ValueError:
#                 continue
    
#     return jsonify(notifications)

# @app.route('/api/dashboard', methods=['GET'])
# @token_required
# def get_dashboard_data(current_user):
#     leads = load_leads()
#     users = load_users()
    
#     # Filter leads by user if not admin
#     if not current_user.get('is_admin'):
#         leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
    
#     # Calculate lead counts by status
#     status_counts = {}
#     for status in STATUS_FLOW.keys():
#         status_counts[status] = len([lead for lead in leads if lead['status'] == status])
    
#     # Calculate lead counts by customer type
#     customer_type_counts = {}
#     for customer_type in CUSTOMER_TYPES:
#         customer_type_counts[customer_type] = len([lead for lead in leads if lead.get('customer_type') == customer_type])
    
#     # Calculate lead counts by user (only for admin)
#     user_lead_counts = []
#     if current_user.get('is_admin'):
#         for user in users:
#             user_leads = [lead for lead in leads if lead.get('created_by') == user['id']]
#             user_status_counts = {}
#             for status in STATUS_FLOW.keys():
#                 user_status_counts[status] = len([lead for lead in user_leads if lead['status'] == status])
            
#             user_lead_counts.append({
#                 'user_id': user['id'],
#                 'user_name': user.get('name', user['username']),
#                 'total_leads': len(user_leads),
#                 'status_counts': user_status_counts
#             })
#     else:
#         # For regular users, show their own stats
#         user_leads = [lead for lead in leads if lead.get('created_by') == current_user['id']]
#         user_status_counts = {}
#         for status in STATUS_FLOW.keys():
#             user_status_counts[status] = len([lead for lead in user_leads if lead['status'] == status])
        
#         user_lead_counts.append({
#             'user_id': current_user['id'],
#             'user_name': current_user.get('name', current_user['username']),
#             'total_leads': len(user_leads),
#             'status_counts': user_status_counts
#         })
    
#     # Calculate recent activity (only show user's leads if not admin)
#     recent_leads = [lead for lead in leads if current_user.get('is_admin') or lead.get('created_by') == current_user['id']]
#     recent_leads = sorted(recent_leads, key=lambda x: x['last_updated'], reverse=True)[:5]
#     recent_leads = [format_lead_details(lead) for lead in recent_leads]
    
#     return jsonify({
#         'status_counts': status_counts,
#         'customer_type_counts': customer_type_counts,
#         'user_lead_counts': user_lead_counts,
#         'recent_leads': recent_leads,
#         'total_leads': len(leads),
#         'total_users': len(users)
#     })

# @app.route('/api/users', methods=['GET'])
# @token_required
# @admin_required
# def get_all_users(current_user):
#     users = load_users()
#     # Remove password hashes before returning
#     for user in users:
#         user.pop('password', None)
#     return jsonify(users)

# @app.route('/api/chat/history', methods=['GET'])
# @token_required
# def get_chat_history(current_user):
#     history = load_chat_history()
#     return jsonify(history)

# if __name__ == '__main__':
#     app.run(debug=True)









import os
import json
import uuid
import faiss
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, make_response
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import csv
from io import StringIO
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'your-secret-key-here'
FAISS_INDEX_PATH = "data/faiss_index.index"
LEADS_FILE = "data/leads.json"
CHAT_HISTORY_FILE = "data/chat_history.json"
USERS_FILE = "data/users.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "your-api-key-here"
EMBEDDING_DIM = 768  # Gemini embedding dimension

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize FAISS with ID mapping
if os.path.exists(FAISS_INDEX_PATH):
    faiss_index = faiss.read_index(FAISS_INDEX_PATH)
else:
    faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(EMBEDDING_DIM))
    os.makedirs("data", exist_ok=True)
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)

# Customer types
CUSTOMER_TYPES = [
    "Builder", "Retail Shop", "Bank", "System Integrator", 
    "Electrical Consultant", "Security Consultant", "Architect", 
    "Government", "Airport", "Distributor"
]

# Currency options
CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SGD"]

# Status workflow
STATUS_FLOW = {
    "Pending": ["Contacted", "Follow-Up", "Interested", "Cancelled", "Rejected"],
    "Contacted": ["Follow-Up", "Interested", "Demo Given", "Cancelled", "Rejected"],
    "Follow-Up": ["Interested", "Demo Given", "Cancelled", "Rejected"],
    "Interested": ["Demo Given", "In Progress", "On Hold"],
    "Demo Given": ["In Progress", "Success", "On Hold"],
    "In Progress": ["Success", "On Hold", "Completed"],
    "On Hold": ["In Progress", "Cancelled"],
    "Success": ["Completed"],
    "Completed": [],
    "Cancelled": [],
    "Rejected": []
}

# Map UUIDs to integer indices for FAISS
id_map = {}  # {uuid_str: int_index}
next_index = 1

# JWT Authentication Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = get_user_by_id(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user['is_admin']:
            return jsonify({'message': 'Admin access required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# Helper Functions
def normalize_lead(lead):
    """Normalize lead data to ensure consistency."""
    normalized = lead.copy()
    if 'name' in normalized and 'client_name' not in normalized:
        normalized['client_name'] = normalized['name']
        del normalized['name']
    if 'company' in normalized and 'company_name' not in normalized:
        normalized['company_name'] = normalized['company']
        del normalized['company']
    if 'project' in normalized and 'project_requirements' not in normalized:
        normalized['project_requirements'] = normalized['project']
        del normalized['project']
    normalized['id'] = str(normalized['id'])
    if 'status' not in normalized:
        normalized['status'] = 'Pending'
    if 'budget' not in normalized:
        normalized['budget'] = 0
    if 'budget_currency' not in normalized:
        normalized['budget_currency'] = 'INR'
    if 'created_at' not in normalized:
        normalized['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    if 'last_updated' not in normalized:
        normalized['last_updated'] = normalized['created_at']
    if 'customer_type' not in normalized:
        normalized['customer_type'] = 'Other'
    if 'assigned_to' not in normalized:
        normalized['assigned_to'] = None
    if 'created_by' not in normalized:
        normalized['created_by'] = None
    if 'cancel_reason' not in normalized:
        normalized['cancel_reason'] = None
    return normalized

def load_leads():
    try:
        with open(LEADS_FILE, 'r') as f:
            data = json.load(f)
            return [normalize_lead(lead) for lead in data] if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_leads(leads):
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2)

def load_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        # Create default admin user if no users exist
        users = [{
            'id': str(uuid.uuid4()),
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'name': 'Admin User',
            'email': 'admin@example.com',
            'is_admin': True,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }]
        save_users(users)
        return users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_by_id(user_id):
    users = load_users()
    return next((user for user in users if user['id'] == user_id), None)

def get_user_by_username(username):
    users = load_users()
    return next((user for user in users if user['username'] == username), None)

def get_embedding(text):
    """Generate embedding for text using Gemini."""
    try:
        result = genai.embed_content(model="models/embedding-001", content=text)
        return np.array(result['embedding'], dtype=np.float32)
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)

def get_faiss_index(lead_id):
    """Map lead ID to FAISS integer index."""
    global next_index
    lead_id_str = str(lead_id)
    if lead_id_str not in id_map:
        id_map[lead_id_str] = next_index
        next_index += 1
    return id_map[lead_id_str]

def index_lead(lead, lead_id):
    """Index lead data in FAISS with embedding."""
    try:
        lead = normalize_lead(lead)
        if not lead.get('client_name'):
            return
        lead_text = f"{lead['client_name']} {lead.get('company_name', '')} {lead.get('project_requirements', '')} {lead.get('notes', '')}"
        embedding = get_embedding(lead_text)
        faiss_index.add_with_ids(embedding.reshape(1, -1), np.array([get_faiss_index(lead_id)], dtype=np.int64))
        faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    except Exception as e:
        logger.error(f"Error indexing lead {lead_id}: {e}")

def reindex_all_leads():
    """Reindex all leads in FAISS."""
    global faiss_index, id_map, next_index
    try:
        faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(EMBEDDING_DIM))
        id_map = {}
        next_index = 1
        leads = load_leads()
        for lead in leads:
            lead_id = lead.get('id')
            if lead_id:
                index_lead(lead, lead_id)
    except Exception as e:
        logger.error(f"Error reindexing leads: {e}")

def get_upcoming_reminders(user_id=None):
    leads = load_leads()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_later = today + timedelta(days=7)
    
    reminders = []
    
    for lead in leads:
        # Filter by user if specified
        if user_id and lead.get('assigned_to') != user_id and lead.get('created_by') != user_id:
            continue
            
        # Meetings today/tomorrow
        if lead.get('meeting_date'):
            try:
                meeting_date = datetime.strptime(lead['meeting_date'], "%Y-%m-%d").date()
                if meeting_date == today:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    reminders.append({
                        'type': 'meeting',
                        'message': f"Meeting with {lead['client_name']} today at {lead.get('meeting_time', '')}{assigned_text}",
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'time': lead.get('meeting_time', ''),
                        'date': lead['meeting_date']
                    })
                elif meeting_date == tomorrow:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    reminders.append({
                        'type': 'meeting',
                        'message': f"Meeting with {lead['client_name']} tomorrow at {lead.get('meeting_time', '')}{assigned_text}",
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'time': lead.get('meeting_time', ''),
                        'date': lead['meeting_date']
                    })
                elif today < meeting_date <= week_later:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    reminders.append({
                        'type': 'meeting',
                        'message': f"Meeting with {lead['client_name']} on {lead['meeting_date']} at {lead.get('meeting_time', '')}{assigned_text}",
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'time': lead.get('meeting_time', ''),
                        'date': lead['meeting_date']
                    })
            except ValueError:
                continue
        
        # Pending review
        if lead.get('status') in ['Pending', 'Follow-Up']:
            try:
                last_updated = datetime.strptime(lead['last_updated'], "%Y-%m-%d %H:%M:%S.%f").date()
                days_since_update = (today - last_updated).days
                if days_since_update >= 5:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    reminders.append({
                        'type': 'review',
                        'message': f"Follow up with {lead['client_name']} (Pending for {days_since_update} days){assigned_text}",
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'days_pending': days_since_update
                    })
            except ValueError:
                continue
    
    return reminders

def format_lead_details(lead):
    """Format lead details for display."""
    lead = normalize_lead(lead)
    created_by = get_user_by_id(lead.get('created_by')) if lead.get('created_by') else None
    assigned_to = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
    
    return {
        'id': lead['id'],
        'client_name': lead['client_name'],
        'company_name': lead.get('company_name', 'N/A'),
        'email': lead.get('email', 'N/A'),
        'phone': lead.get('phone', 'N/A'),
        'project_requirements': lead.get('project_requirements', 'N/A'),
        'status': lead['status'],
        'budget': lead.get('budget', 0),
        'budget_currency': lead.get('budget_currency', 'INR'),
        'probability': lead.get('probability', 'N/A'),
        'meeting_date': lead.get('meeting_date', 'N/A'),
        'meeting_time': lead.get('meeting_time', ''),
        'notes': lead.get('notes', 'N/A'),
        'created_at': lead['created_at'],
        'last_updated': lead['last_updated'],
        'customer_type': lead.get('customer_type', 'Other'),
        'created_by': created_by['name'] if created_by else 'N/A',
        'created_by_id': lead.get('created_by'),
        'assigned_to': assigned_to['name'] if assigned_to else 'N/A',
        'assigned_to_id': lead.get('assigned_to'),
        'cancel_reason': lead.get('cancel_reason', 'N/A')
    }

def generate_gemini_response(query, leads):
    """Generate response using Gemini with lead context."""
    try:
        # Format leads for context
        leads_context = "\n".join([
            f"Lead ID: {lead['id']}, Client: {lead['client_name']}, Company: {lead.get('company_name', 'N/A')}, "
            f"Status: {lead['status']}, Probability: {lead.get('probability', 'N/A')}%, "
            f"Budget: {lead.get('budget', 0)} {lead.get('budget_currency', 'INR')}, "
            f"Meeting: {lead.get('meeting_date', 'N/A')} at {lead.get('meeting_time', 'N/A')}, "
            f"Project: {lead.get('project_requirements', 'N/A')}, Notes: {lead.get('notes', 'N/A')}"
            for lead in leads
        ])
        
        # Generate prompt
        prompt = f"""
        You are an AI lead management assistant. Based on the following query and lead data, provide a concise and accurate response.
        
        Query: {query}
        
        Lead Data:
        {leads_context}
        
        Instructions:
        1. For listing requests, show relevant leads with key details including budget
        2. For filtering requests, apply the filter and show results
        3. For status changes, verify the transition is valid
        4. For meeting scheduling, confirm details are complete
        5. Always be concise and factual
        6. Include reminders if any are upcoming
        
        Current Date: {datetime.now().strftime("%Y-%m-%d")}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating Gemini response: {e}")
        return "Sorry, I couldn't generate a response due to an error."

def execute_operation(query, user_id=None):
    """Execute operation using Gemini's understanding."""
    leads = load_leads()
    
    # Filter leads by user if not admin
    if user_id:
        users = load_users()
        current_user = next((u for u in users if u['id'] == user_id), None)
        if not current_user.get('is_admin'):
            leads = [lead for lead in leads if lead.get('created_by') == user_id or lead.get('assigned_to') == user_id]
    
    reminders = get_upcoming_reminders(user_id)
    
    # First get Gemini's response
    initial_response = generate_gemini_response(query, leads)
    
    # Check if response indicates an action needs to be taken
    if any(keyword in initial_response.lower() for keyword in ["update", "change", "schedule", "create", "delete"]):
        # Get confirmation from Gemini on the action
        confirmation_prompt = f"""
        Based on this response to the query "{query}":
        {initial_response}
        
        Should any data be updated in the lead management system? 
        If yes, provide the exact changes in JSON format with:
        - operation: "create"/"update"/"delete"
        - lead_id: (if applicable)
        - field: (if updating)
        - new_value: (if updating)
        - new_lead_data: (if creating)
        """
        
        try:
            confirmation = model.generate_content(confirmation_prompt)
            if "{" in confirmation.text and "}" in confirmation.text:
                # Extract JSON from response
                start = confirmation.text.index("{")
                end = confirmation.text.rindex("}") + 1
                action = json.loads(confirmation.text[start:end])
                
                # Execute the action
                if action.get("operation") == "update":
                    leads = load_leads()
                    lead = next((l for l in leads if str(l['id']) == action.get("lead_id")), None)
                    if lead:
                        lead[action.get("field")] = action.get("new_value")
                        lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        save_leads(leads)
                        index_lead(lead, lead['id'])
                
                elif action.get("operation") == "create":
                    new_lead = action.get("new_lead_data", {})
                    new_lead['id'] = str(uuid.uuid4())
                    new_lead['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    new_lead['last_updated'] = new_lead['created_at']
                    leads.append(new_lead)
                    save_leads(leads)
                    index_lead(new_lead, new_lead['id'])
                
                elif action.get("operation") == "delete":
                    leads = [l for l in leads if str(l['id']) != action.get("lead_id")]
                    save_leads(leads)
                    faiss_index.remove_ids(np.array([get_faiss_index(action.get("lead_id"))], dtype=np.int64))
        
        except Exception as e:
            logger.error(f"Error executing action: {e}")
    
    # Add reminders to response if any
    if reminders:
        initial_response += "\n\nReminders:\n" + "\n".join([r['message'] for r in reminders])
    
    return initial_response

# Authentication Routes
@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify', 'error': 'Login required!'}), 401
    
    user = get_user_by_username(auth['username'])
    
    if not user:
        return jsonify({'message': 'Could not verify', 'error': 'User not found!'}), 401
    
    if check_password_hash(user['password'], auth['password']):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'is_admin': user.get('is_admin', False)
            }
        })
    
    return jsonify({'message': 'Could not verify', 'error': 'Wrong password!'}), 401

@app.route('/api/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    data = request.json
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required!'}), 400
    
    if get_user_by_username(data['username']):
        return jsonify({'message': 'User already exists!'}), 400
    
    hashed_password = generate_password_hash(data['password'])
    
    new_user = {
        'id': str(uuid.uuid4()),
        'username': data['username'],
        'password': hashed_password,
        'name': data.get('name', ''),
        'email': data.get('email', ''),
        'is_admin': data.get('is_admin', False),
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    }
    
    users = load_users()
    users.append(new_user)
    save_users(users)
    
    return jsonify({
        'message': 'User created successfully!',
        'user': {
            'id': new_user['id'],
            'username': new_user['username'],
            'name': new_user['name'],
            'email': new_user['email'],
            'is_admin': new_user['is_admin']
        }
    })

# Lead Management Routes
@app.route('/')
def home():
    try:
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, 'w') as f:
                json.dump([], f)
        if not os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'w') as f:
                json.dump([], f)
        if not os.path.exists(USERS_FILE):
            load_users()  # This will create default admin user
        reindex_all_leads()
        return '<h1>backend working</h1>';
    except Exception as e:
        logger.error(f"Error initializing home route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    chat_history = load_chat_history()
    
    try:
        # Handle status change commands directly
        if any(cmd in user_message.lower() for cmd in ["change status", "update status", "mark as", "move to"]):
            leads = load_leads()
            client_name = None
            new_status = None
            
            # Extract client name and new status from message
            parts = user_message.lower().split()
            for i, part in enumerate(parts):
                if part in ["to", "as"] and i < len(parts)-1:
                    new_status = parts[i+1].capitalize()
                elif part not in ["change", "status", "update", "mark", "move"]:
                    if not client_name:
                        client_name = part.capitalize()
            
            # Find the lead
            lead = next((l for l in leads if l['client_name'].lower().startswith(client_name.lower())), None)
            
            if not lead:
                return jsonify({'response': f"No lead found for client {client_name}"})
            
            # Validate status transition
            current_status = lead['status']
            if new_status not in STATUS_FLOW.get(current_status, []):
                return jsonify({'response': f"Cannot change status from {current_status} to {new_status}"})
            
            # Update status
            lead['status'] = new_status
            lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            save_leads(leads)
            
            response = f"Lead {lead['id']} ({lead['client_name']}) status changed from {current_status} to {new_status}"
            reminders = get_upcoming_reminders(current_user['id'])
            if reminders:
                response += "\n\nReminders:\n" + "\n".join([r['message'] for r in reminders])
            
            chat_history.append({
                'user': user_message,
                'bot': response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            })
            save_chat_history(chat_history)
            
            return jsonify({'response': response})
        
        # Handle list commands
        elif "list all" in user_message.lower() or "show all" in user_message.lower():
            status = None
            if "pending" in user_message.lower():
                status = "Pending"
            elif "contacted" in user_message.lower():
                status = "Contacted"
            elif "follow-up" in user_message.lower():
                status = "Follow-Up"
            elif "interested" in user_message.lower():
                status = "Interested"
            
            leads = load_leads()
            # Filter by user if not admin
            if not current_user.get('is_admin'):
                leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
            
            if status:
                filtered_leads = [l for l in leads if l['status'] == status]
            else:
                filtered_leads = leads
            
            response = f"{status if status else 'All'} Leads:\n\n" if filtered_leads else "No leads found\n"
            for lead in filtered_leads:
                response += f"* **Lead ID:** {lead['id']}, **Client:** {lead['client_name']}, **Company:** {lead.get('company_name', 'N/A')}, "
                response += f"**Status:** {lead['status']}, **Probability:** {lead.get('probability', 'N/A')}%, "
                response += f"**Budget:** {lead.get('budget', 0)} {lead.get('budget_currency', 'INR')}, "
                meeting_info = f"{lead.get('meeting_date', 'N/A')} at {lead.get('meeting_time', 'N/A')}" if lead.get('meeting_date') else "None"
                response += f"**Meeting:** {meeting_info}\n"
            
            reminders = get_upcoming_reminders(current_user['id'])
            if reminders:
                response += "\nReminders:\n" + "\n".join([r['message'] for r in reminders])
            
            chat_history.append({
                'user': user_message,
                'bot': response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            })
            save_chat_history(chat_history)
            
            return jsonify({'response': response})
        
        # Handle show lead command
        elif user_message.lower().startswith('show lead'):
            lead_name = user_message[10:].strip()
            leads = load_leads()
            # Filter by user if not admin
            if not current_user.get('is_admin'):
                leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
            
            matching_leads = [l for l in leads if lead_name.lower() in l['client_name'].lower()]
            
            if not matching_leads:
                response = f"No leads found matching '{lead_name}'"
            elif len(matching_leads) == 1:
                response = format_lead_details(matching_leads[0])
            else:
                response = f"Multiple leads found matching '{lead_name}':\n"
                for lead in matching_leads:
                    response += f"- {lead['client_name']} (ID: {lead['id']}, Status: {lead['status']})\n"
                response += "\nPlease specify which lead you want to see."
            
            chat_history.append({
                'user': user_message,
                'bot': response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            })
            save_chat_history(chat_history)
            
            return jsonify({'response': response})
        
        # Handle add notes command
        elif "add notes" in user_message.lower() or "update notes" in user_message.lower():
            parts = user_message.split()
            lead_name = None
            notes_start = None
            
            # Find where the notes start
            for i, part in enumerate(parts):
                if part.lower() in ["notes", "note"] and i < len(parts)-1:
                    notes_start = i+1
                    break
            
            # Find lead name before "notes"
            for i, part in enumerate(parts):
                if part.lower() in ["notes", "note"]:
                    lead_name = " ".join(parts[:i])
                    break
            
            if not lead_name or not notes_start:
                response = "Please specify both the lead name and the notes to add."
            else:
                leads = load_leads()
                # Filter by user if not admin
                if not current_user.get('is_admin'):
                    leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
                
                lead = next((l for l in leads if lead_name.lower() in l['client_name'].lower()), None)
                
                if not lead:
                    response = f"No lead found matching '{lead_name}'"
                else:
                    notes = " ".join(parts[notes_start:])
                    lead['notes'] = notes
                    lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    save_leads(leads)
                    index_lead(lead, lead['id'])
                    response = f"Notes updated for {lead['client_name']} (ID: {lead['id']})"
            
            chat_history.append({
                'user': user_message,
                'bot': response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            })
            save_chat_history(chat_history)
            
            return jsonify({'response': response})
        
        # Default to Gemini for other queries
        else:
            response = execute_operation(user_message, current_user['id'])
            
            chat_history.append({
                'user': user_message,
                'bot': response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            })
            save_chat_history(chat_history)
            
            return jsonify({'response': response})
    
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads', methods=['GET'])
@token_required
def get_all_leads(current_user):
    leads = load_leads()
    
    # Filter by user if not admin
    if not current_user.get('is_admin'):
        leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
    
    return jsonify([format_lead_details(lead) for lead in leads])

@app.route('/api/leads/<lead_id>', methods=['GET'])
@token_required
def get_lead(current_user, lead_id):
    leads = load_leads()
    lead = next((l for l in leads if str(l['id']) == lead_id), None)
    
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    # Check permission if not admin
    if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify(format_lead_details(lead))

@app.route('/api/leads', methods=['POST'])
@token_required
def create_lead(current_user):
    try:
        data = request.json
        if not data.get('client_name'):
            return jsonify({'error': 'Client name is required'}), 400
            
        lead_id = str(uuid.uuid4())
        new_lead = {
            'id': lead_id,
            'client_name': data.get('client_name'),
            'company_name': data.get('company_name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'project_requirements': data.get('project_requirements'),
            'status': data.get('status', 'Pending'),
            'budget': data.get('budget', 0),
            'budget_currency': data.get('budget_currency', 'INR'),
            'probability': data.get('probability', 50),
            'meeting_date': data.get('meeting_date'),
            'meeting_time': data.get('meeting_time'),
            'notes': data.get('notes'),
            'customer_type': data.get('customer_type', 'Other'),
            'created_by': current_user['id'],
            'assigned_to': data.get('assigned_to'),
            'cancel_reason': data.get('cancel_reason'),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
        
        leads = load_leads()
        leads.append(new_lead)
        save_leads(leads)
        index_lead(new_lead, lead_id)
        
        return jsonify({
            'success': True,
            'message': f"Lead created for {new_lead['client_name']}",
            'lead': format_lead_details(new_lead)
        })
        
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<lead_id>', methods=['PUT'])
@token_required
def update_lead(current_user, lead_id):
    try:
        data = request.json
        leads = load_leads()
        lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
        if lead_index is None:
            return jsonify({'error': 'Lead not found'}), 404
            
        lead = leads[lead_index]
        
        # Check permission if not admin
        if not current_user.get('is_admin') and lead.get('created_by') != current_user['id']:
            return jsonify({'error': 'Unauthorized to update this lead'}), 403
        
        # Update status if provided and valid
        if 'status' in data:
            current_status = lead['status']
            if data['status'] in STATUS_FLOW.get(current_status, []):
                lead['status'] = data['status']
            else:
                return jsonify({'error': f'Invalid status transition from {current_status} to {data["status"]}'}), 400
        
        # Update other fields
        for field in ['client_name', 'company_name', 'email', 'phone', 'project_requirements',
                     'meeting_date', 'meeting_time', 'probability', 'notes', 'customer_type',
                     'assigned_to', 'cancel_reason', 'budget', 'budget_currency']:
            if field in data:
                lead[field] = data[field]
        
        lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        leads[lead_index] = lead
        save_leads(leads)
        
        # Reindex lead in FAISS
        faiss_index.remove_ids(np.array([get_faiss_index(lead_id)], dtype=np.int64))
        index_lead(lead, lead_id)
        
        return jsonify({
            'success': True,
            'message': f"Lead updated for {lead['client_name']}",
            'lead': format_lead_details(lead)
        })
        
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<lead_id>', methods=['DELETE'])
@token_required
def delete_lead(current_user, lead_id):
    try:
        leads = load_leads()
        lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
        if lead_index is None:
            return jsonify({'error': 'Lead not found'}), 404
            
        lead = leads[lead_index]
        
        # Check permission if not admin
        if not current_user.get('is_admin') and lead.get('created_by') != current_user['id']:
            return jsonify({'error': 'Unauthorized to delete this lead'}), 403
            
        faiss_index.remove_ids(np.array([get_faiss_index(lead_id)], dtype=np.int64))
        deleted_lead = leads.pop(lead_index)
        save_leads(leads)
        
        return jsonify({
            'success': True,
            'message': f"Lead deleted for {deleted_lead['client_name']}"
        })
        
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<lead_id>/status', methods=['PUT'])
@token_required
def update_lead_status(current_user, lead_id):
    try:
        data = request.json
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
            
        leads = load_leads()
        lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
        if lead_index is None:
            return jsonify({'error': 'Lead not found'}), 404
            
        lead = leads[lead_index]
        
        # Check permission if not admin
        if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
            return jsonify({'error': 'Unauthorized to update this lead'}), 403
            
        current_status = lead['status']
        new_status = data['status']
        
        if new_status not in STATUS_FLOW.get(current_status, []):
            return jsonify({'error': f'Invalid status transition from {current_status} to {new_status}'}), 400
        
        lead['status'] = new_status
        lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        leads[lead_index] = lead
        save_leads(leads)
        
        # Reindex lead in FAISS
        faiss_index.remove_ids(np.array([get_faiss_index(lead_id)], dtype=np.int64))
        index_lead(lead, lead_id)
        
        return jsonify({
            'success': True,
            'message': f"Status updated to {new_status} for {lead['client_name']}",
            'lead': format_lead_details(lead)
        })
        
    except Exception as e:
        logger.error(f"Error updating status for lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<lead_id>/reminder', methods=['POST'])
@token_required
def add_reminder(current_user, lead_id):
    try:
        data = request.json
        if not data.get('date') or not data.get('time'):
            return jsonify({'error': 'Date and time are required'}), 400
            
        leads = load_leads()
        lead_index = next((i for i, lead in enumerate(leads) if str(lead['id']) == lead_id), None)
        
        if lead_index is None:
            return jsonify({'error': 'Lead not found'}), 404
            
        lead = leads[lead_index]
        
        # Check permission if not admin
        if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
            return jsonify({'error': 'Unauthorized to set reminder for this lead'}), 403
            
        if 'reminders' not in lead:
            lead['reminders'] = []
            
        reminder = {
            'date': data['date'],
            'time': data['time'],
            'note': data.get('note', ''),
            'created_by': current_user['id'],
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
        
        lead['reminders'].append(reminder)
        lead['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        leads[lead_index] = lead
        save_leads(leads)
        
        return jsonify({
            'success': True,
            'message': f"Reminder added for {lead['client_name']}",
            'reminder': reminder
        })
        
    except Exception as e:
        logger.error(f"Error adding reminder for lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/export', methods=['POST'])
@token_required
def export_leads(current_user):
    data = request.json
    leads = load_leads()
    
    # Filter by user if not admin
    if not current_user.get('is_admin'):
        leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
    
    # Filter leads if parameters provided
    if data.get('lead_id'):
        leads = [lead for lead in leads if str(lead['id']) == data['lead_id']]
    elif data.get('status'):
        leads = [lead for lead in leads if lead['status'] == data['status']]
    elif data.get('customer_type'):
        leads = [lead for lead in leads if lead.get('customer_type') == data['customer_type']]
    
    if not leads:
        return jsonify({'error': 'No leads found'}), 404
    
    # Create a StringIO object for CSV
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow([
        'ID', 'Client Name', 'Company Name', 'Email', 'Phone', 
        'Project Requirements', 'Status', 'Probability', 'Budget', 'Budget Currency',
        'Customer Type', 'Meeting Date', 'Meeting Time', 'Notes', 'Created By', 
        'Assigned To', 'Cancel Reason', 'Created At', 'Last Updated'
    ])
    
    # Write data
    for lead in leads:
        created_by = get_user_by_id(lead.get('created_by')) if lead.get('created_by') else None
        assigned_to = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
        
        writer.writerow([
            lead['id'],
            lead['client_name'],
            lead.get('company_name', ''),
            lead.get('email', ''),
            lead.get('phone', ''),
            lead.get('project_requirements', ''),
            lead['status'],
            lead.get('probability', ''),
            lead.get('budget', ''),
            lead.get('budget_currency', 'INR'),
            lead.get('customer_type', ''),
            lead.get('meeting_date', ''),
            lead.get('meeting_time', ''),
            lead.get('notes', ''),
            created_by['name'] if created_by else '',
            assigned_to['name'] if assigned_to else '',
            lead.get('cancel_reason', ''),
            lead['created_at'],
            lead['last_updated']
        ])
    
    # Prepare response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=leads_export_{datetime.now().strftime('%Y%m%d')}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    leads = load_leads()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_later = today + timedelta(days=7)
    
    notifications = {
        'today': [],
        'tomorrow': [],
        'upcoming': [],
        'pending_review': []
    }
    
    for lead in leads:
        # Filter by user if not admin
        if not current_user.get('is_admin') and lead.get('created_by') != current_user['id'] and lead.get('assigned_to') != current_user['id']:
            continue
            
        # Meetings today/tomorrow
        if lead.get('meeting_date'):
            try:
                meeting_date = datetime.strptime(lead['meeting_date'], "%Y-%m-%d").date()
                if meeting_date == today:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    notifications['today'].append({
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'time': lead.get('meeting_time', ''),
                        'type': 'meeting',
                        'assigned_to': lead.get('assigned_to'),
                        'assigned_text': assigned_text
                    })
                elif meeting_date == tomorrow:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    notifications['tomorrow'].append({
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'time': lead.get('meeting_time', ''),
                        'type': 'meeting',
                        'assigned_to': lead.get('assigned_to'),
                        'assigned_text': assigned_text
                    })
                elif today < meeting_date <= week_later:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    notifications['upcoming'].append({
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'date': lead['meeting_date'],
                        'time': lead.get('meeting_time', ''),
                        'type': 'meeting',
                        'assigned_to': lead.get('assigned_to'),
                        'assigned_text': assigned_text
                    })
            except ValueError:
                continue
        
        # Pending review
        if lead['status'] == 'Pending':
            try:
                created_date = datetime.strptime(lead['created_at'], "%Y-%m-%d %H:%M:%S.%f").date()
                days_pending = (today - created_date).days
                if days_pending >= 5:
                    assigned_user = get_user_by_id(lead.get('assigned_to')) if lead.get('assigned_to') else None
                    assigned_text = f" (Assigned to: {assigned_user['name']})" if assigned_user else ""
                    notifications['pending_review'].append({
                        'lead_id': lead['id'],
                        'client_name': lead['client_name'],
                        'days_pending': days_pending,
                        'type': 'review',
                        'assigned_to': lead.get('assigned_to'),
                        'assigned_text': assigned_text
                    })
            except ValueError:
                continue
    
    return jsonify(notifications)

@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard_data(current_user):
    leads = load_leads()
    users = load_users()
    
    # Filter leads by user if not admin
    if not current_user.get('is_admin'):
        leads = [lead for lead in leads if lead.get('created_by') == current_user['id'] or lead.get('assigned_to') == current_user['id']]
    
    # Calculate lead counts by status
    status_counts = {}
    for status in STATUS_FLOW.keys():
        status_counts[status] = len([lead for lead in leads if lead['status'] == status])
    
    # Calculate lead counts by customer type
    customer_type_counts = {}
    for customer_type in CUSTOMER_TYPES:
        customer_type_counts[customer_type] = len([lead for lead in leads if lead.get('customer_type') == customer_type])
    
    # Calculate total budget by status
    budget_by_status = {}
    for status in STATUS_FLOW.keys():
        status_leads = [lead for lead in leads if lead['status'] == status]
        budget_by_status[status] = sum(lead.get('budget', 0) for lead in status_leads)
    
    # Calculate lead counts by user (only for admin)
    user_lead_counts = []
    if current_user.get('is_admin'):
        for user in users:
            user_leads = [lead for lead in leads if lead.get('created_by') == user['id']]
            user_status_counts = {}
            for status in STATUS_FLOW.keys():
                user_status_counts[status] = len([lead for lead in user_leads if lead['status'] == status])
            
            user_lead_counts.append({
                'user_id': user['id'],
                'user_name': user.get('name', user['username']),
                'total_leads': len(user_leads),
                'status_counts': user_status_counts
            })
    else:
        # For regular users, show their own stats
        user_leads = [lead for lead in leads if lead.get('created_by') == current_user['id']]
        user_status_counts = {}
        for status in STATUS_FLOW.keys():
            user_status_counts[status] = len([lead for lead in user_leads if lead['status'] == status])
        
        user_lead_counts.append({
            'user_id': current_user['id'],
            'user_name': current_user.get('name', current_user['username']),
            'total_leads': len(user_leads),
            'status_counts': user_status_counts
        })
    
    # Calculate recent activity (only show user's leads if not admin)
    recent_leads = [lead for lead in leads if current_user.get('is_admin') or lead.get('created_by') == current_user['id']]
    recent_leads = sorted(recent_leads, key=lambda x: x['last_updated'], reverse=True)[:5]
    recent_leads = [format_lead_details(lead) for lead in recent_leads]
    
    return jsonify({
        'status_counts': status_counts,
        'customer_type_counts': customer_type_counts,
        'budget_by_status': budget_by_status,
        'user_lead_counts': user_lead_counts,
        'recent_leads': recent_leads,
        'total_leads': len(leads),
        'total_users': len(users)
    })

@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    users = load_users()
    # Remove password hashes before returning
    for user in users:
        user.pop('password', None)
    return jsonify(users)

@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_chat_history(current_user):
    history = load_chat_history()
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True)