package envoy.authz

import input.attributes.request.http as http_request

default allow = false

token = {
    "valid": valid, 
    "payload": payload, 
    "method": http_request.method, 
    "path": http_request.path ,
    "bearer": bearer
    } {
    [bearer, encoded] := split(http_request.headers.authorization, " ")
    [valid, _, payload] := io.jwt.decode_verify(encoded, {"secret": "secret"})
}

allow{
action_allowed
}

# ---------------------------------------------------------------
# Python microservices rules (client-app / server-app)
# ---------------------------------------------------------------

# Allow GET on /api/client/v1 for role "guest"
action_allowed {
  token.method == "GET"
  token.payload.role == "guest"
  glob.match("/api/client/v1", [], token.path)
}

# Allow GET on /api/server/v1 for role "guest"
action_allowed {
  token.method == "GET"
  token.payload.role == "guest"
  glob.match("/api/server/v1", [], token.path)
}

# Allow POST on /api/client/v1 for role "guest"
action_allowed {
  token.method == "POST"
  token.payload.role == "guest"
  glob.match("/api/client/v1", [], token.path)
}

# Allow POST on /api/server/v1 for role "guest"
action_allowed {
  token.method == "POST"
  token.payload.role == "guest"
  glob.match("/api/server/v1", [], token.path)
}

# Health endpoints and root are always allowed (no JWT required)
allow {
  glob.match("/health*", [], http_request.path)
}

allow {
  http_request.path == "/"
}
