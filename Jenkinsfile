// Jenkinsfile
// Jenkins Pipeline for methodology-v2 Enforcement

pipeline {
    agent {
        label 'methodology-enforcement'
    }
    
    options {
        // 失敗後不自動清理
        preserveStashes()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    stages {
        stage('Constitution Check') {
            steps {
                echo '📜 Running Constitution Check...'
                sh 'python3 cli.py constitution verify || exit 1'
            }
        }
        
        stage('Policy Engine') {
            steps {
                echo '⚙️ Running Policy Engine...'
                sh 'python3 cli.py policy --strict || exit 1'
            }
        }
        
        stage('Quality Gate') {
            steps {
                echo '🎯 Running Quality Gate...'
                sh 'python3 cli.py quality gate || exit 1'
            }
        }
        
        stage('Security Scan') {
            steps {
                echo '🔒 Running Security Scan...'
                sh 'python3 cli.py security scan || exit 1'
            }
        }
    }
    
    post {
        success {
            echo '🎉 All enforcement checks passed!'
        }
        failure {
            echo '❌ Enforcement check failed'
            // 發送通知
        }
    }
}
