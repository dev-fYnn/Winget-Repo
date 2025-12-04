import base64
import secrets

from fastapi import APIRouter, Form, HTTPException, Depends, Request, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from Modules.API.Filter import LoginResponse, ClientVersionResponse, Package, package_version_form_data, Package_Version
from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import parse_version, decode_flask_cookie
from Modules.Login.Functions import check_Credentials
from Modules.Packages.Functions import get_package_service, add_package_service, edit_package_service, delete_package_service, delete_package_versions_service, add_package_version_service
from Modules.User.Functions import user_setup_finished, check_User_Exists
from Modules.Winget.Functions import authorize_IP_Range, get_winget_Settings, authenticate_Client
from settings import PATH_LOGOS


client_api_bp = APIRouter()
oauth2_scheme = HTTPBearer(auto_error=False)


class APICheckerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not user_setup_finished():
            return JSONResponse(status_code=503, content={"error": "Setup incomplete"})

        client_ip = request.client.host
        if not authorize_IP_Range(client_ip):
            raise HTTPException(status_code=403, detail="IP address not authorized")

        if request.url.path.lower() in ["/client/api/docs", "/client/api/redoc", "/client/api/openapi.json"]:
            flask_cookies = decode_flask_cookie(request.cookies.get('Winget-Repo'))
            status, _ = check_User_Exists('', user_id=flask_cookies.get('logged_in', ''))
            if not status:
                return RedirectResponse(url=f"{request.base_url.scheme}://{request.base_url.components.netloc}/", status_code=307)
        return await call_next(request)


async def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    if credentials:
        token = credentials.credentials
        db = SQLiteDatabase()
        try:
            session = db.get_Session_Token(token)
            if not session:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            db.update_Session_Timestamp(token)
            return token
        finally:
            del db
    raise HTTPException(status_code=401, detail="Invalid or expired token")


# LOGIN
@client_api_bp.post("/login", tags=["Authentication"], summary="Authenticate user and generate a session token", response_model=LoginResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    """
    Authenticates a user using a username and password.

    If the credentials are valid, a new session token is generated and returned.
    If the credentials are invalid, a **401 Unauthorized** error is returned.

    **Parameters:**
    - **username**: The user's login name
    - **password**: The user's password

    **Returns:**
    - JSON object containing the generated session token
    """
    db = SQLiteDatabase()
    exists, user_id = check_Credentials(username, password)
    if exists:
        token = db.create_Session_Token(user_id, secrets.token_urlsafe(32))
        del db
        return JSONResponse(content={"message": token}, status_code=200)
    del db
    raise HTTPException(status_code=401, detail="Unauthorized")


# LOGOUT
@client_api_bp.post("/logout", tags=["Authentication"], summary="Terminate an active user session")
async def logout(token: str = Form(...)):
    """
    Deletes the provided session token from the database.

    The logout request is always treated as successful,
    even if the provided token does not exist or is already invalid.

    **Parameters:**
    - **token**: The session token to invalidate

    **Returns:**
    - JSON confirmation message
    """
    db = SQLiteDatabase()
    exists = db.get_Session_Token(token)
    if exists:
        db.delete_Session_Token(token=token)
    del db
    return JSONResponse(content={"message": "Logout Successful!"}, status_code=200)


# NUR Bearer Token
@client_api_bp.get("/test", tags=["Authentication"], summary="Check API availability and authentication functionality")
async def test(token: str = Depends(verify_bearer_token)):
    """
    Performs a simple API functionality test.

    This endpoint is protected and requires a valid **Bearer token**.
    It is commonly used for health monitoring or verifying authentication flow.

    **Parameters:**
    - **token**: Bearer token from the Authorization header

    **Returns:**
    - Confirmation message indicating the API is operational
    """
    return {"Message": "Its working!"}


# Bearer oder Auth-Token
@client_api_bp.post("/client_version", tags=["Winget-Repo Client"], summary="Winget-Repo Client Version", response_model=ClientVersionResponse)
async def client_version(request: Request, auth_token: Optional[str] = Form(None), client: Optional[int] = Form(None), token_auth: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)):
    """
    Returns the latest available version of the Winget-Repo Client.
    Checks Bearer Token first, then 'Auth-Token' in body.
    """
    db = SQLiteDatabase()
    settings = get_winget_Settings()
    if bool(int(settings.get("CLIENT_AUTHENTICATION", "0"))):
        if token_auth:
            try:
                session = db.get_Session_Token(token_auth.credentials)
                if not session:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                db.update_Session_Timestamp(token_auth.credentials)
            finally:
                del db
        else:
            try:
                client_value = client if client else 0
                client_ip = request.client.host
                if not authenticate_Client(auth_token, client_ip, settings, client_value):
                    raise HTTPException(status_code=401, detail="Invalid Auth-Token")
            finally:
                del db
    else:
        del db
    return JSONResponse(content={"Version": "2.5.0.0"}, status_code=200)


# Bearer oder Auth-Token – Packages
@client_api_bp.post("/get_packages", tags=["Packages"], summary="Retrieve all available packages including versions and logos", response_model=list[Package])
async def get_packages(request: Request, include_disabled: bool=False, auth_token: Optional[str] = Form(None), client: Optional[int] = Form(None), token_auth: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)):
    """
    Returns a complete list of all available packages including metadata,
    available versions, and Base64-encoded package logos.

    If client authentication is enabled, client-specific blacklist rules apply
    and certain packages may be filtered out based on the authentication token.

    **Parameters:**
    - **auth**: Authentication token (Bearer or Client Auth-Token)
    - **include_disabled**: If `True`, disabled packages will also be included

    **Returns:**
    - JSON list of package objects containing full metadata
    """
    db = SQLiteDatabase()
    settings = get_winget_Settings()
    if bool(int(settings.get("CLIENT_AUTHENTICATION", "0"))):
        if token_auth:
            try:
                session = db.get_Session_Token(token_auth.credentials)
                if not session:
                    del db
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                db.update_Session_Timestamp(token_auth.credentials)
            finally:
                pass
        else:
            try:
                client_value = client if client else 0
                client_ip = request.client.host
                if not authenticate_Client(auth_token, client_ip, settings, client_value):
                    del db
                    raise HTTPException(status_code=401, detail="Invalid Auth-Token")
            finally:
                pass

    try:
        data = db.get_All_Packages(include_disabled)
        for d in data:
            versions = db.get_All_Versions_from_Package(d["PACKAGE_ID"])
            version_dummy = sorted(((v["VERSION"], v["UID"]) for v in versions), key=lambda x: parse_version(x[0]), reverse=True)
            d["VERSIONS"] = [item[0] for item in version_dummy]
            d["VERSIONS_UID"] = [item[1] for item in version_dummy]

            logo_name = d.get("PACKAGE_LOGO", "dummy.png")
            logo_path = Path(PATH_LOGOS) / logo_name

            if logo_path.exists():
                encoded_logo = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
                d["PACKAGE_LOGO"] = f"data:image/png;base64,{encoded_logo}"
            else:
                d["PACKAGE_LOGO"] = ""
        if auth_token:
            blacklist = db.get_Blacklist_for_client(auth_token)
            data = [d for d in data if d["PACKAGE_ID"] not in blacklist]
        return JSONResponse(content=data, status_code=200)
    finally:
        del db


# Bearer
@client_api_bp.post("/add_package", tags=["Packages"], summary="Add a new package", response_model=list[Package])
async def add_package(package_id: str = Form(...), package_name: str = Form(...), package_publisher: str = Form(...), package_description: str = Form(...), Logo: Optional[UploadFile] = File(None), token: str = Depends(verify_bearer_token)):
    """
    Returns a complete list of all available packages including metadata,
    available versions, and Base64-encoded package logos.

    If client authentication is enabled, client-specific blacklist rules apply
    and certain packages may be filtered out based on the authentication token.

    **Parameters:**
    - **auth**: Authentication token (Bearer or Client Auth-Token)
    - **include_disabled**: If `True`, disabled packages will also be included

    **Returns:**
    - JSON list of package objects containing full metadata
    """
    data = {"package_id": package_id, "package_name": package_name, "package_publisher": package_publisher, "package_description": package_description}
    package = get_package_service(data.get("package_id", ''))
    if package:
        raise HTTPException(status_code=401, detail="Package ID already available!")

    if len(data) > 0:
        status, package_id = add_package_service(data, Logo)
        if status:
            return JSONResponse(content={"Message": "Package was added successfully!"}, status_code=200)
        else:
            raise HTTPException(status_code=401, detail="Package can't be created. Try again!")
    else:
        raise HTTPException(status_code=404, detail="Error. No Data found!")


# Bearer
@client_api_bp.patch("/edit_package/{package_id}", tags=["Packages"], summary="Edit an existing package", response_model=dict)
async def edit_package(package_id: str, package_name: str = Form(...), package_publisher: str = Form(...), package_description: str = Form(...), Logo: Optional[UploadFile] = File(None), token: str = Depends(verify_bearer_token)):
    """
    Edits the details of an existing package including name, publisher, description, and logo.

    **Parameters:**
    - **package_id**: ID of the package to edit
    - **package_name**: Updated name
    - **package_publisher**: Updated publisher
    - **package_description**: Updated description
    - **Logo**: Updated logo file

    **Returns:**
    - JSON message confirming package update
    """
    data = {
        "package_name": package_name,
        "package_publisher": package_publisher,
        "package_description": package_description
    }

    package = get_package_service(package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found!")

    status, _ = edit_package_service(package_id, data, Logo)
    if status:
        return JSONResponse(content={"Message": "Package was updated successfully!"}, status_code=200)
    else:
        raise HTTPException(status_code=400, detail="Changes could not be saved. Try again!")


# Bearer
@client_api_bp.delete("/delete_package/{package_id}", tags=["Packages"], summary="Delete an existing package", response_model=dict)
async def delete_package(package_id: str, token: str = Depends(verify_bearer_token)):
    """
    Deletes an existing package by its ID.

    **Parameters:**
    - **package_id**: ID of the package to delete

    **Returns:**
    - JSON message confirming package deletion
    """
    status = delete_package_service(package_id)
    if status:
        return JSONResponse(content={"Message": "Package was deleted successfully!"}, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Package not found!")


# Bearer
@client_api_bp.get("/get_package_versions/{package_id}", tags=["Package Versions"], summary="Retrieve all available versions from a package", response_model=list[Package_Version])
async def get_package_versions(package_id: str, token: str = Depends(verify_bearer_token)):
    """
    Returns a complete list of all available versions from a package.

    **Parameters:**
    - **package_id**: ID of the package

    **Returns:**
    - JSON list of package version objects containing full metadata
    """
    db = SQLiteDatabase()
    try:
        data = db.get_All_Versions_from_Package(package_id)
        if data:
            for d in data:
                d['NESTED_PACKAGE_INSTALLER_PATHS'] = db.get_Nested_Installer(d['UID'])
        return JSONResponse(content=data, status_code=200)
    finally:
        del db


@client_api_bp.get("/get_specific_package_version/{version_uid}", tags=["Package Versions"], summary="Retrieve a specific version from a package", response_model=Package_Version)
async def get_specific_package_version(version_uid: str, token: str = Depends(verify_bearer_token)):
    """
    Returns a specific version from a package.

    **Parameters:**
    - **version_uid**: UID of the package version

    **Returns:**
    - JSON String of a package version objects containing full metadata
    """
    db = SQLiteDatabase()
    try:
        data = db.get_specfic_Versions_from_Package(version_uid)
        if data:
            data['NESTED_PACKAGE_INSTALLER_PATHS'] = db.get_Nested_Installer(data['UID'])
        return JSONResponse(content=data, status_code=200)
    finally:
        del db


# Bearer
@client_api_bp.post("/add_package_version/{package_id}", tags=["Package Versions"], summary="Add a new package version", response_model=dict)
async def add_package_version(package_id: str, file: UploadFile = File(...), token: str = Depends(verify_bearer_token), data: dict = Depends(package_version_form_data)):
    """
    Adds a new version to an existing package, including file upload and optional switches.

    **Parameters:**
    - **package_id**: ID of the package
    - **file**: File of the new version
    - **data**: Metadata and switches for the new version

    **Returns:**
    - JSON message confirming version addition and the new version UID
    """
    if not file or not data:
        raise HTTPException(status_code=400, detail="File or data is missing!")

    try:
        status, message_or_uid = add_package_version_service(package_id, data, file)
    except Exception:
        raise HTTPException(status_code=500, detail="Error creating the package version.")

    if status:
        return JSONResponse(content={"Message": "Package version was added successfully!", "UID": message_or_uid}, status_code=201)
    else:
        if "already exists" in message_or_uid:
            raise HTTPException(status_code=409, detail=message_or_uid)
        elif "doesn't exist" in message_or_uid:
            raise HTTPException(status_code=404, detail=message_or_uid)
        else:
            raise HTTPException(status_code=400, detail=message_or_uid)


# Bearer
@client_api_bp.delete("/delete_package_version/{package_id}", tags=["Package Versions"], summary="Delete package versions", response_model=dict)
async def delete_package_version(package_id: str, versions_uids: list[str] = Form(...), token: str = Depends(verify_bearer_token)):
    """
    Deletes one or more versions of a package by their UIDs.

    **Parameters:**
    - **package_id**: ID of the package
    - **versions_uids**: List of version UIDs to delete

    **Returns:**
    - JSON message confirming deletion
    """
    package = get_package_service(package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found!")

    if not versions_uids:
        raise HTTPException(status_code=400, detail="No versions selected!")

    if len(versions_uids) == 1 and "," in versions_uids[0]:
        versions_uids = [v.strip() for v in versions_uids[0].split(",")]

    delete_package_versions_service(versions_uids)
    return JSONResponse(content={"Message": "Package versions deleted successfully!"}, status_code=200)
