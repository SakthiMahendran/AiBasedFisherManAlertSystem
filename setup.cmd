@echo off

:: Start script
echo Starting project setup...

:: Execute backend commands in the current directory
echo Installing Python dependencies...
pip install -r requirements.txt || (echo Failed to install Python dependencies! && exit /b 1)

echo Running database migrations...
python manage.py makemigrations || (echo Failed to run 'makemigrations'! && exit /b 1)
python manage.py migrate || (echo Failed to run 'migrate'! && exit /b 1)

echo Backend setup complete!

:: Navigate to frontend and install npm dependencies
echo Navigating to frontend folder...
cd frontend || (echo Failed to navigate to 'frontend' folder! && exit /b 1)

echo Installing npm dependencies...
npm install || (echo Failed to install npm dependencies! && exit /b 1)

echo Frontend setup complete!

:: Navigate back to root
cd ..

echo Project setup completed successfully!

:: End script
exit /b 0
