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
                sh 'python3 --version'
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Test/Validate') {
            steps {
                sh 'python3 -m py_compile main.py'
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t shadow-quest:ci .'
            }
        }

        stage('Result') {
            steps {
                echo 'SUCCESS: Shadow Quest was checked out, built, validated, and packaged as a Docker image.'
            }
        }
    }
}