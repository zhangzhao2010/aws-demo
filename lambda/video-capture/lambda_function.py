import boto3
import json

def get_response_body(error_no=0, error_msg='', data={}):
    return {
        'error_no': error_no,
        'error_msg': error_msg,
        'data': data
    }

def get_response(error_no, error_msg, data = {}):
    response_body = get_response_body(error_no, error_msg, data)
    return {
        'statusCode': 200,
        'headers':{
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(response_body),
    }

# handler
def lambda_handler(event, context):
    aws_request_id = context.aws_request_id
     
    try:
        return get_response(0, '', {})
        pass
    except Exception as e:
        return get_response(1, str(e))

if __name__ == '__main__':
    # lambda_handler({}, {})
    pass