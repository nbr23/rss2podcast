pipeline {
	agent any

	options {
		ansiColor('xterm')
		disableConcurrentBuilds()
	}

	stages {
		stage('Test') {
			steps {
				script {
					def testImage = docker.build("rss2podcast-test:${env.BUILD_ID}", "--target test -f Dockerfile .")
					testImage.inside {
						sh 'uv run --group test pytest'
					}
				}
			}
			post {
				always {
					sh "docker rmi rss2podcast-test:${env.BUILD_ID} || true"
				}
			}
		}

		stage('Sync github repo') {
				when { branch 'master' }
				steps {
						syncRemoteBranch('git@github.com:nbr23/rss2podcast.git', 'master')
				}
		}

	}
}
