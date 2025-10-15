import duo_client
import qrcode
import requests
import os

# Load Duo credentials from environment variables
ikey = os.environ.get("DUO_IKEY")
skey = os.environ.get("DUO_SKEY")
host = os.environ.get("DUO_HOST")

Cikey = os.environ.get("DUO_CLIENT_IKEY")
Cskey = os.environ.get("DUO_CLIENT_SKEY")
Chost = os.environ.get("DUO_CLIENT_HOST")

# Validate that all required environment variables are set
if not all([ikey, skey, host, Cikey, Cskey, Chost]):
    raise Exception("Missing required Duo API credentials in environment variables. Please check your .env file.")

# Initialize the Duo client
duo_admin = duo_client.Admin(
    ikey=ikey,
    skey=skey,
    host=host
)

auth_client = duo_client.Auth(
    ikey=Cikey,
    skey=Cskey,
    host=Chost
)


def generate_duo_activation_url(phone_id):
    """
    Retrieve the activation URL for a phone using the duo_admin.json_api_call 
    method, which handles signing and authentication.
    """
    try:
        # Use the duo_admin client's json_api_call method
        response = duo_admin.json_api_call(
            'POST',
            f'/admin/v1/phones/{phone_id}/activation_url',
            {}  # no body needed
        )
        
        activation_url = response.get("activation_url")
        if not activation_url:
            raise ValueError("No activation_url returned by Duo.")
        
        print(f"Activation URL generated: {activation_url}")
        return activation_url

    except Exception as e:
        print(f"Error generating activation URL: {e}")
        raise


async def enroll_user_with_duo(username):
    """
    Enroll the user with Duo:
    1. Add the user via the Admin API.
    2. Add a phone (no real phone number, just a generic smartphone for Duo Mobile).
    3. Associate the phone with the user.
    4. Retrieve an activation URL for the device.
    5. Generate a QR code from the activation URL.
    """
    try:
        # Step 1: Add the user in Duo (ensure username is unique)
        user_response = duo_admin.add_user(username=username)
        user_id = user_response["user_id"]
        print(f"User '{username}' added to Duo with ID: {user_id}")

        # Step 2: Add a "generic smartphone" as a phone device
        # Make sure the type and platform are correct. 
        # According to Duo docs, 'type' can be "mobile" for smartphones.
        phone_response = duo_admin.add_phone(
            number="",  # No phone number
            type="mobile",
            platform="generic smartphone",
            name=f"{username}'s Smartphone"
        )
        phone_id = phone_response["phone_id"]
        print(f"Generic smartphone added with ID: {phone_id}")

        # Step 3: Link the phone to the user
        duo_admin.add_user_phone(user_id=user_id, phone_id=phone_id)
        print(f"Phone ID {phone_id} linked to user ID {user_id}.")

        # Step 4: Generate activation URL
        activation_url = generate_duo_activation_url(phone_id)

        # Step 5: Generate a QR code from the activation URL
        # Ensure static/duo_qr directory exists
        qr = qrcode.make(activation_url)
        qr_dir = "static/duo_qr"
        os.makedirs(qr_dir, exist_ok=True)  # Create the directory if it doesn't exist
        qr_path = os.path.join(qr_dir, f"{username}_duo_qr.png")
        qr.save(qr_path)
        print(f"QR Code saved at: {qr_path}")

        return qr_path
    except Exception as e:
        print(f"Error during Duo enrollment: {e}")
        raise


async def send_duo_push(username):
    """
    Send a Duo Push to the user via the Auth API.
    """
    try:
        # Check preauth first
        preauth_response = auth_client.preauth(username=username)
        if preauth_response["result"] == "auth":
            # Initiate a push authentication
            auth_response = auth_client.auth(
                username=username,
                factor="push",
                device="auto"
            )
            if auth_response["result"] == "allow":
                print("Duo Push approved.")
                return True
            else:
                print(f"Duo push rejected or failed: {auth_response}")
                return False
        else:
            print(f"Duo preauth failed or user not enrolled: {preauth_response}")
            return False
    except Exception as e:
        print(f"Error during Duo push: {e}")
        return False
