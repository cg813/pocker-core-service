def gv
pipeline{
    agent { label 'master' }
    environment {
        SERVER_CREDENTIALS = credentials('jenkins-gcr-account')
    }
    stages{
        stage("Load script") {
            steps {
                script {
                    gv = load "script.groovy"
                    env.GIT_COMMIT_MSG = sh (script: 'git log -1 --pretty=%B ${GIT_COMMIT} | head -n1', returnStdout: true).stripIndent().trim()
                    env.GIT_AUTHOR = sh (script: 'git log -1 --pretty=%ae ${GIT_COMMIT} | awk -F "@" \'{print $1}\' | grep -Po "[a-z]{1,}" | head -n1', returnStdout: true).trim()

                }
            }
        }
        stage("Build Image for dev") {
            when {
                branch 'dev'
            }
            agent { label "builder" }
            steps {
              slackSend (color: '#00FF00', message: "build - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started  ${env.BUILD_NUMBER}  by changes from ${env.GIT_AUTHOR} commit message ${env.GIT_COMMIT_MSG} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nBuild started by changes from ${env.GIT_AUTHOR} commit message is ${env.GIT_COMMIT_MSG} : ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')
                script {
                    gv.buildImageDev()
                }
            }
        }
        stage("Build Image for prod") {
            when {
                branch 'master'
            }
            agent { label "builder" }
            steps {
              slackSend (color: '#00FF00', message: "build - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started  ${env.BUILD_NUMBER}  by changes from ${env.GIT_AUTHOR} commit message ${env.GIT_COMMIT_MSG} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nBuild started by changes from ${env.GIT_AUTHOR} commit message is ${env.GIT_COMMIT_MSG} : ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')
                script {
                    gv.buildImageProd()
                }
            }
        }
        stage("Feature test") {
            when {
                not {
                    anyOf {
                        branch 'dev'
                        branch 'master'
                    }
                }
            }
            agent { label "builder" }
            steps {
              slackSend (color: '#00FF00', message: "Unit Test  - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started  ${env.BUILD_NUMBER} for user: ${env.GIT_AUTHOR} commit message ${env.GIT_COMMIT_MSG} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \n Unit Test  started by changes ${env.GIT_AUTHOR} commit message ${env.GIT_COMMIT_MSG} : ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')
                script {
                    gv.buildImageTest()
                    gv.TestApp()
                }
            }
        }
        stage("Backend test") {
            when {
                anyOf {
                    branch 'dev'
                    branch 'master'
                }
            }
            agent { label "builder" }
            steps {
              slackSend (color: '#00FF00', message: "Backend test  - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started  ${env.BUILD_NUMBER}  in order to check changes from user:  ${env.GIT_AUTHOR} commit message ${env.GIT_COMMIT_MSG} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nUnit Test  started by changes ${env.GIT_AUTHOR} commit message is ${env.GIT_COMMIT_MSG} : ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')
                script {
                    gv.TestApp()
                }
            }
        }
        stage("Push dev image to Repo") {
            when {
                branch 'dev'
            }
            agent { label "builder" }
            steps {
              slackSend (color: '#00FF00', message: "Push tested ${env.BRANCH_NAME} image to repo No - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nPush image to repo  ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')

                script {
                    gv.PushImagetgoDev()
                }
            }
        }
        stage("Push prod image to Repo") {
            when {
                branch 'master'
            }
            agent { label "builder" }
            steps {
              slackSend (color: '#00FF00', message: "Push tested ${env.BRANCH_NAME} image to repo # - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nPush image to repo  ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')
                script {
                    gv.PushImagetgoProd()
                }
            }
        }
        stage("Deploy to Development") {
            when {
                branch 'dev'
            }
            steps {
              slackSend (color: '#00FF00', message: "Start deploy to development from branch${env.BRANCH_NAME} build No # - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nDeployment to development  ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')
                script {
                    gv.deployToDev()
                }
            }
        }
        stage("Deploy to production") {
            when {
                branch 'master'
            }
            steps {
              slackSend (color: '#00FF00', message: "Start deploy to production from branch ${env.BRANCH_NAME} build No # - ${env.BUILD_NUMBER} ${env.JOB_NAME} Started ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)")
              discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nDeployment to production  ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')

                script {
                    gv.DeployToProd()
                }
            }
        }
    }
      
    post {
    success {
      slackSend (color: '#00FF00', message: "Success  job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (<${env.BUILD_URL}|Open>)")
      discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nSuccess ${env.BUILD_NUMBER} \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')

    }
    failure {
      slackSend (color: '#FF0000', message: "Failed: job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (<${env.BUILD_URL}|Open>)")
      discordSend(description: "${currentBuild.currentResult}: Job ${env.JOB_NAME} \nFailed ${env.BUILD_NUMBER} changes fromk user ${env.GIT_AUTHOR} not valid \nMore info at: \n${env.BUILD_URL}", footer: 'No-Code', unstable: true, link: env.BUILD_URL, result: "${currentBuild.currentResult}", title: "${JOB_NAME} << CLICK", webhookURL: 'https://discord.com/api/webhooks/928581745308209172/48mS1wvOi8G_iBP6Tu6ZbsbB9adCpXT2dR-uLZXP7wwLof2d-2qypkFixEvGBKxULa_L')

    }
  }
}
