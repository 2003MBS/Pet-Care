import qrcode
from qrcode.constants import ERROR_CORRECT_H

# Create QR code instance
qr = qrcode.QRCode(
    version=1,
    error_correction=ERROR_CORRECT_H,
    box_size=10,
    border=4,
)

# Add the UPI payment data
# Using a demo UPI ID for PawSphere
upi_data = "upi://pay?pa=pawsphere@upi&pn=PawSphere&mc=5999&tid=123456789&tr=Invoice123&tn=Pet%20Products%20Payment"

qr.add_data(upi_data)
qr.make(fit=True)

# Create the QR code image with custom colors
qr_image = qr.make_image(fill_color="#3498db", back_color="white")

# Save the QR code
qr_image.save("static/img/pawsphere-qr.png") 