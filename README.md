# Talk to My CV

A web application that allows users to interact with a chatbot representing a professional profile. The chatbot is designed to answer questions about the profile's career, background, skills, and experience in a professional and engaging manner.

## Features

- **Interactive Chat Interface**: Built with Gradio, providing a user-friendly chat experience.
- **Professional Profile Representation**: The chatbot acts as a representative of a professional profile, answering questions based on the provided profile information.
- **Quality Control**: An evaluator agent ensures that the responses are acceptable and professional, with feedback for improvement if needed.
- **Docker Support**: Containerized deployment for easy setup and scalability.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd talk-to-my-cv
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add the following variables:
     ```
     OPENAI_API_KEY=your_openai_api_key
     GEMINI_API_KEY=your_gemini_api_key
     ```

## Usage

1. Ensure your profile information is set up:
   - Update `data/name.txt` with the name of the profile.
   - Update `data/profile.md` with the professional background details.

2. Run the application:
   ```bash
   python src/main.py
   ```

3. Open your web browser and navigate to the provided URL (usually `http://localhost:7860`).

4. Start chatting with the bot!

## Deployment

### Docker

1. Build the Docker image:
   ```bash
   docker build -t talk-to-my-cv .
   ```

2. Run the container:
   ```bash
   docker run -p 7860:7860 talk-to-my-cv
   ```

3. Access the application at `http://localhost:7860`.

## Project Structure

- `src/`: Contains the main application code.
  - `main.py`: Entry point for the application.
  - `agents/`: Contains the chat and evaluator agents.
  - `models/`: Contains the data models.
  - `utils/`: Contains utility functions.
- `data/`: Contains the profile information.
- `Dockerfile`: Configuration for Docker deployment.
- `requirements.txt`: List of Python dependencies.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 