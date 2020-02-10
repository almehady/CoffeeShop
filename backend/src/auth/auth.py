import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'mehady.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffeeshop'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    try:
        # attempt to get the header from the request
        auth_headers = request.headers['Authorization']
        # split bearer and the token
        header_parts = auth_headers.split(' ')
    except:
        # raise an AuthError if no header is present
        if request.headers is None:
            raise AuthError({
                'code': 'no_request_header',
                'description': 'There is no header on this request.'
            }, 401)
        if 'Authorization' not in request.headers:
            raise AuthError({
                'code': 'no_auth_in_header',
                'description': 'No authorization details in request header.'
            }, 401)
        # raise an AuthError if the header is malformed
        if len(header_parts) != 2:
            raise AuthError({
                'code': 'too_many_parts',
                'description': 'Too many parts to Auth header.'
            }, 401)
        if header_parts[0].lower() != 'bearer':
            raise AuthError({
                'code': 'no_bearer_tag',
                'description': 'Bearer tag not present or malformed.'
            }, 401)

    # return the token part of the header
    return(header_parts[1])



'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    # raise an AuthError if permissions are not included in the payload
    if 'permissions' not in payload:
                        raise AuthError({
                            'code': 'invalid_claims',
                            'description': 'Permissions not included in JWT.'
                        }, 400)
# raise an AuthError if the requested permission string is not in the payload permissions array
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not in payload.'
        }, 401)
    return True


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)

    # CHOOSE OUR KEY
    rsa_key = {}
    # check it is an Auth0 token with key id (kid)
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        # verify the token using Auth0 /.well-known/jwks.json
        if key['kid'] == unverified_header['kid']:
            # decode the payload from the token
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    # Finally, verify!!!
    if rsa_key:
        # validate the claims
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            # return the decoded payload
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    # decorators take in the function (f) which they decorate
    def requires_auth_decorator(f):
        # need wraps method to be imported from functools
        @wraps(f)
        # define wrapper, takes in a couple of optional arguments (+args, ++kwargs)
        def wrapper(*args,  **kwargs):
            # add function need to call within wrapper
            jwt = get_token_auth_header()
            try:
                # checking token is valid
                payload = verify_decode_jwt(jwt)
            except:
                raise AuthError({
                    'code': 'invalid_token',
                    'description': 'Invalid token.'
                }, 401)
            check_permissions(permission, payload)
            # wrapper returns function with the arguments (provide jwt as a parameter to calling function)
            return f(payload, *args,  **kwargs)
        # requires_auth returns the wrapper
        return wrapper
    return requires_auth_decorator

