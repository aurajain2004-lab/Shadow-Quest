pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                bat 'python --version'
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Test/Validate') {
            steps {
                bat 'python -m py_compile main.py'
            }
        }

        stage('Docker Build') {
            steps {
                bat 'docker build -t shadow-quest:ci .'
            }
        }

        stage('Result') {
            steps {
                echo 'SUCCESS: Shadow Quest was checked out, built, validated, and packaged as a Docker image.'
            }
        }
    }
}