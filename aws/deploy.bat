
set /p BOT_NAME="Enter AWS lambda name: "

echo "Preparing dependencies..."
rmdir package
pip install --target ./package googletrans==3.1.0a0
pip install --target ./package requests
cd package
echo "Creating update zip..."
zip -r ../deployment-package.zip *
cd ..
zip -g deployment-package.zip lambda_function.py
echo "Uploading zip to AWS lambda..."
aws lambda update-function-code --function-name %BOT_NAME% --zip-file fileb://deployment-package.zip
