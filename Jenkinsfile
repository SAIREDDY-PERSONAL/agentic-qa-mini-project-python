pipeline {
    agent {
        docker {
            image 'mcr.microsoft.com/playwright/python:v1.63.0-noble'
            args '-u root'
        }
    }

    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -e ".[dev]"'
            }
        }

        stage('Lint & Type-check') {
            steps {
                sh 'ruff check . && ruff format --check . && mypy'
            }
        }

        stage('Run Agentic Tests') {
            steps {
                sh 'pytest --html=reports/report.html --self-contained-html'
            }
        }
    }

    post {
        always {
            publishHTML(target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'report.html',
                reportName: 'Playwright & LLM Eval Report'
            ])

            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
    }
}
