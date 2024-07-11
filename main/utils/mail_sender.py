from django.core.mail import send_mail

from main import settings


class MailSender:
    from_email = settings.EMAIL_HOST_USER

    def send_otp(self, subject, otp, recipient_list):
        html = """
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 0;
                    }
            
                    .container {
                        background-color: #ffffff;
                        border-radius: 5px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        margin: 20px auto;
                        max-width: 600px;
                        padding: 20px;
                    }
            
                    .content {
                        text-align: center;
                    }
            
                    .title {
                        font-size: 24px;
                        margin-bottom: 20px;
                    }
            
                    .message {
                        font-size: 16px;
                        margin-bottom: 30px;
                        color: #555;
                    }
            
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        font-size: 18px;
                        font-weight: bold;
                        text-decoration: none;
                        background-color: #28c69f; /* Google Blue */
                        color: #ffffff;
                        border-radius: 5px;
                    }
            
                    .header {
                        margin-bottom: 10px;
                        color: #28c69f;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="content">
                        <!-- Replace 'your_base64_encoded_image_string' with your actual base64-encoded image string -->
                        <div class="header">
                            <h1>iDARP</h1>
                        </div>
                        <div class="title">%s</div>
                        <div class="message">
                            Your One-Time Password (OTP) is: <strong><h2>%s</h2></strong>.
                        </div>
                    </div>
                </div>
            </body>
            </html>
        """
        html_message = html % (subject, otp)
        return send_mail(subject, "", self.from_email, recipient_list, html_message=html_message, fail_silently=False)

    def send_html(self, subject, message, recipient_list):
        html = """
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 0;
                    }
            
                    .container {
                        background-color: #ffffff;
                        border-radius: 5px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        margin: 20px auto;
                        max-width: 600px;
                        padding: 20px;
                    }
            
                    .content {
                        text-align: center;
                    }
            
                    .title {
                        font-size: 24px;
                        margin-bottom: 20px;
                    }
            
                    .message {
                        font-size: 16px;
                        margin-bottom: 30px;
                        color: #555;
                    }
            
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        font-size: 18px;
                        font-weight: bold;
                        text-decoration: none;
                        background-color: #28c69f; /* Google Blue */
                        color: #ffffff;
                        border-radius: 5px;
                    }
            
                    .header {
                        margin-bottom: 10px;
                        color: #28c69f;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="content">
                        <!-- Replace 'your_base64_encoded_image_string' with your actual base64-encoded image string -->
                        <div class="header">
                            <h1>iDARP</h1>
                        </div>
                        <div class="title">%s</div>
                        <div class="message">
                            %s
                        </div>
                    </div>
                </div>
            </body>
            </html>
        """
        html_message = html % (subject, message)
        return send_mail(subject, "", self.from_email, recipient_list, html_message=html_message, fail_silently=False)

    def send_plain(self, subject, message, recipient_list):
        return send_mail(subject, message, self.from_email, recipient_list, fail_silently=False)
