from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import oracledb as cx_Oracle
import requests
from datetime import datetime

import urllib.parse

app = FastAPI()
# connection = cx_Oracle.connect(
#     'unicacrm/unicacrm@unicadbinstance.c5udahrktbeq.us-east-2.rds.amazonaws.com:1521/unicadb')
# cursor = connection.cursor()


def to_snake_case(text):
    """
    Convert text to snake case.
    """
    words = text.split()
    return '_'.join(words).lower()

created_on_date = datetime.now().date()
def insert_data(data):
    new_data = {}
    for key, value in data.items():
        if key == "Country/Region":
            key = "INDIVIDUAL_COUNTRY"
        new_key = to_snake_case(key)
        new_data[new_key] = value
    print("new_data", new_data)


    new_data['created_on_date'] =created_on_date
    # Prepare the SQL statement
    sql = """
        INSERT INTO event_stage (
            FIRST_NAME,
            LAST_NAME,
            PHONE_NUMBER,
            INDIVIDUAL_COUNTRY,
            JOB_ROLE,
            COMPANY_NAME,
            EMAIL_ADDRESS,
            UTM_SOURCE,
            EVENT_NAME,
            CAMPAIGN_CODE,
            OFFER_CODE,
            LEAD_SOURCE,
            LOAD_SOURCE,
            SOURCE_NAME,
            FED_FLAG,
            HCL_PRODUCT,
            DESCRIPTION,
            UTM_CAMPAIGN,
            UTM_MEDIUM,
            LEAD_RATING,
            EMAIL_PERMISSION,
            PHONE_PERMISSION,
            EVENT_ID,
            PRIVACY_STMT_ACK,
            CREATED_ON_DATE
        ) VALUES (
            :first_name,
            :last_name,
            :phone_number,
            :individual_country,
            :job_title,
            :company_name,
            :work_email,
            :utm_source,
            :event_name,
            :campaign_code,
            :offer_code,
            :lead_source,
            'LinkedInForm',
            :source_name,
            :fed_flag,
            :hcl_product,
            :description,
            :utm_campaign,
            :utm_medium,
            :lead_rating,
            'Yes',
            'Yes',
            :id,
            'Yes',
            :created_on_date
        )
    """
    # Check if the record already exists
    existing_sql = """
        SELECT COUNT(*) FROM EVENT_STAGE
        WHERE EVENT_ID = :id
    """
    # cursor.execute(existing_sql, {'id': new_data['id']})
    # result = cursor.fetchone()
    # record_exists = result[0] > 0

    print(new_data,'here1')
    # print(record_exists,'record_exists')


    # if not record_exists:
    #     # Execute the SQL statement with the data
    #     cursor.execute(sql, new_data)

    #     # Commit the transaction
    #     connection.commit()
    # else:
    #     print("Record already exists.")


# Your LinkedIn application credentials
CLIENT_ID = '862b890ei7k2ez'
CLIENT_SECRET = 'tqKaP8ZHTGpJsdjM'
# 'https://oauth.pstmn.io/v1/browser-callback' This should be registered in your LinkedIn app settings
REDIRECT_URI = 'http://localhost:8000/callback'
STATE = 'STATE'  # A unique string to prevent CSRF attacks
# The scopes you need
SCOPE = 'r_ads,r_organization_admin,r_liteprofile,r_marketing_leadgen_automation,r_events'


@app.get("/")
def read_root():
    return {"message": "Welcome to the LinkedIn Auth Code Generator!"}


@app.get("/login")
def login():
    # Construct the authorization URL
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'state': STATE,
        'scope': SCOPE
    }

    url = 'https://www.linkedin.com/oauth/v2/authorization?' + \
        urllib.parse.urlencode(params)

    print(url)

    # Redirect the user to LinkedIn's authorization endpoint
    return url


@app.get("/callback")
def callback(request: Request):
    # LinkedIn will redirect the user back to this endpoint with the authorization code
    auth_code = request.query_params.get('code')
    state = request.query_params.get('state')

    # Verify the state to protect against CSRF attacks
    if state != STATE:
        return {"error": "Invalid state parameter"}

    print(auth_code)

    # Display the authorization code (you could also exchange it for an access token here)
    return {"authorization_code": auth_code}


# define api method  an endpoint that will take the authorization code and exchange it for an access token
@app.get("/get_access_token")
def get_access_token(code: str):
    # Construct the URL to exchange the authorization code for an access token
    url = 'https://www.linkedin.com/oauth/v2/accessToken'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    # Make a POST request to the access token endpoint
    response = requests.post(url, headers=headers, data=data)

    # Display the access token
    return response.json()


@app.get("/get_leads")
def get_lead_responses(access_token: str):
    baseUrl = "https://api.linkedin.com/rest"
    sponsoredaccount_id = "508278638"
    leadtype_sponsored = "SPONSORED"
    timerange_start = 1715937337000
    timerange_end = 1718197899000
    url = f"{baseUrl}/leadFormResponses?q=owner&owner=(sponsoredAccount:urn%3Ali%3AsponsoredAccount%3A{sponsoredaccount_id})&leadType=(leadType:{leadtype_sponsored})&limitedToTestLeads=false&submittedAtTimeRange=(start:{timerange_start},end:{timerange_end})&fields=ownerInfo,associatedEntityInfo,leadMetadataInfo,owner,leadType,versionedLeadGenFormUrn,id,submittedAt,testLead,formResponse,form:(hiddenFields,creationLocale,name,id,content)&count=10&start=0"
    headers = {
        'Authorization': f"Bearer {access_token}",
        'LinkedIn-Version': '202403',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    response = requests.get(url, headers=headers)
    print("formresp")
    json_data = response.json()
    print(json_data)
    leads_list = []
    for form in json_data['elements']:
        form_answers = form['formResponse']['answers']
        form_questions = form['form']['content']['questions']
        form_hidden_fields = form['form']['hiddenFields']

        # Creating dictionaries using comprehensions
        ans_dict = {ans['questionId']: ans['answerDetails']
                    ['textQuestionAnswer']['answer'] for ans in form_answers}
        q_dict = {q['questionId']: q['name'] for q in form_questions}
        # Mapping questions to their answers
        q_ans_dict = {q_dict[key]: ans_dict[key]
                      for key in q_dict if key in ans_dict}
        for key in form_hidden_fields:
            q_ans_dict[key['name']] = key['value']

        q_ans_dict['id'] = form['id']

        leads_list.append(q_ans_dict)
        insert_data(q_ans_dict)

      # Close the cursor and connection
    # cursor.close()
    # connection.close()

    return leads_list
