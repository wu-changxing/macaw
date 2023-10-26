# Project Macaw

Welcome to Project Macaw, the robust and dynamic backend powering the EchoAtrium Community. This project is designed to provide a seamless, efficient, and scalable backend solution, leveraging modern technologies and frameworks to meet the diverse needs of the EchoAtrium community.

## Key Features

Project Macaw brings a range of functionalities to the EchoAtrium community:

1. **Django Wagtail Framework**: At its core, Macaw uses Django Wagtail, offering a powerful and flexible CMS for content management and administrative tasks.
2. **Django REST Framework (DRF)**: Utilizes DRF to serve and handle JSON data efficiently, ensuring seamless frontend-backend integration.
3. **Socket.IO Integration**: Implements Socket.IO for real-time message handling, enhancing the chat and instant messaging features.
4. **Redis Server**: Employs a Redis server for managing time-consuming tasks, ensuring high performance and scalability.
5. **Transition from Celery**: Originally using Celery for task management, Macaw has evolved to leverage Redis for more efficient handling of background tasks.
6. **Email Notification System**: Features a robust email notification system, keeping users informed and engaged.
7. **Localization Support**: Offers extensive localization with support for 10 languages, making the platform globally accessible.
8. **ChatGPT Plugin**: Includes a ChatGPT plugin for translating blog content, enhancing accessibility and user engagement.
9. **Wallet Comments System**: Integrates a unique wallet comments system, adding an innovative layer to user interactions.

## Getting Started

### Prerequisites

- Python 3.x
- Django
- Redis server

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/project-macaw.git
   cd project-macaw
   ```

2. **Set Up a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**

   Set up your `.env` file with the necessary configurations (e.g., database settings, API keys).

5. **Run Migrations**

   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server**

   ```bash
   python manage.py runserver
   ```

   The server will start on `http://localhost:8000`.

## Contributing

Contributions to Project Macaw are welcome! Whether it's bug fixes, feature enhancements, or documentation improvements, your help is appreciated.

- **Fork the Repository**: Start by forking the repository and making your changes.
- **Pull Requests**: Submit a pull request with a clear description of your changes.

## Localization

Project Macaw's localization efforts are ongoing. If you're fluent in any of the supported languages and wish to contribute, please reach out.

## License

This project is licensed under MIT. Please see the LICENSE file for more details.

## Acknowledgments

- A big thank you to the EchoAtrium community and all contributors who have made Project Macaw what it is today.
