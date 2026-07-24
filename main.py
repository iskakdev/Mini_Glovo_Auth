from fastapi import FastAPI
from api import (user_profile, auth)
import uvicorn

mini_glovo_app = FastAPI(title='Mini Glovo Auth')
mini_glovo_app.include_router(user_profile.user_services_router)

mini_glovo_app.include_router(auth.auth_router)


if __name__ == '__main__':
    uvicorn.run(mini_glovo_app, host='127.0.0.1', port=8000)
