import os
from flask import Flask, request
from twilio.util import TwilioCapability
from twilio.rest import Client
import twilio.twiml

# Account Sid and Auth Token can be found in your account dashboard
ACCOUNT_SID = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
AUTH_TOKEN = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

# TwiML app outgoing connections will use
APP_SID = 'APZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ'

CALLER_ID = '+12345678901'
CLIENT = 'jenny'
account_sid = ACCOUNT_SID
auth_token  = AUTH_TOKEN
workspace_sid = "{{ workspace_sid }}"
workflow_sid = "{{ workflow_sid }}"

app = Flask(__name__)

@app.route('/token')
def token():
  account_sid = os.environ.get("ACCOUNT_SID", ACCOUNT_SID)
  auth_token = os.environ.get("AUTH_TOKEN", AUTH_TOKEN)
  app_sid = os.environ.get("APP_SID", APP_SID)

  capability = TwilioCapability(account_sid, auth_token)

  # This allows outgoing connections to TwiML application
  if request.values.get('allowOutgoing') != 'false':
     capability.allow_client_outgoing(app_sid)

  # This allows incoming connections to client (if specified)
  client = request.values.get('client')
  if client != None:
    capability.allow_client_incoming(client)

  # This returns a token to use with Twilio based on the account and capabilities defined above
  return capability.generate()

@app.route('/call', methods=['GET', 'POST'])
def call():
  """ This method routes calls from/to client                  """
  """ Rules: 1. From can be either client:name or PSTN number  """
  """        2. To value specifies target. When call is coming """
  """           from PSTN, To value is ignored and call is     """
  """           routed to client named CLIENT                  """
  resp = twilio.twiml.Response()
  from_value = request.values.get('From')
  to = request.values.get('To')
  if not (from_value and to):
    resp.say("Invalid request")
    return str(resp)
  from_client = from_value.startswith('client')
  caller_id = os.environ.get("CALLER_ID", CALLER_ID)
  if not from_client:
    # PSTN -> client
    resp.dial(callerId=from_value).client(CLIENT)
  elif to.startswith("client:"):
    # client -> client
    resp.dial(callerId=from_value).client(to[7:])
  else:
    # client -> PSTN
    resp.dial(to, callerId=caller_id)
  return str(resp)
@app.route("/assignment_callback", methods=['GET', 'POST'])
def assignment_callback():
    """Respond to assignment callbacks with an acceptance and 200 response"""

    ret = '{"instruction": "accept"}'
    resp = Response(response=ret, status=200, mimetype='application/json')
    return resp

@app.route("/create_task", methods=['GET', 'POST'])
def create_task():
    """Creating a Task"""
    task = client.taskrouter.workspace(workspace_sid) \
                 .tasks.create(workflow_sid=workflow_sid,
                               attributes='{"selected_language":"es"}')

    print(task.attributes)
    resp = Response({}, status=200, mimetype='application/json')
    return resp

@app.route("/accept_reservation", methods=['GET', 'POST'])
def accept_reservation():
    """Accepting a Reservation"""
    task_sid = request.args.get('task_sid')
    reservation_sid = request.args.get('reservation_sid')

    reservation = client.taskrouter.workspaces(workspace_sid) \
                                   .tasks(task_sid) \
                                   .reservations(reservation_sid) \
                                   .update(reservation_status='accepted')

    print(reservation.reservation_status)
    print(reservation.worker_name)

    resp = Response({}, status=200, mimetype='application/json')
    return resp

@app.route('/', methods=['GET', 'POST'])
def welcome():
  resp = twilio.twiml.Response()
  resp.say("Welcome to Twilio")
  return str(resp)

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
