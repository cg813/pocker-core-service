def buildImageDev() {
    echo "Starting application build"
    withCredentials([file(credentialsId: 'jenkins-gcr-account', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
        sh 'docker login -u _json_key -p "`cat ${GOOGLE_APPLICATION_CREDENTIALS}`" https://gcr.io'
        sh 'docker build -f backend/core/Dockerfile backend/core/ -t backend'
        sh 'docker tag backend gcr.io/mima-325516/texas/backend:dev'
        sh 'docker tag backend gcr.io/mima-325516/texas/worker:dev'
    }
    echo "Image pushed to AWS"
}

def buildImageTest() {
    echo "Starting application build"
    withCredentials([file(credentialsId: 'jenkins-gcr-account', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
        sh 'export GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}'
        sh 'docker login -u _json_key -p "`cat ${GOOGLE_APPLICATION_CREDENTIALS}`" https://gcr.io'
        sh 'docker build -f backend/core/Dockerfile backend/core/ -t backend'
        sh 'docker tag backend gcr.io/mima-325516/texas/backend:test'
        sh 'docker tag backend gcr.io/mima-325516/texas/worker:test'
    }
    echo "Test Image pushed to Google container registry"
}

def buildImageProd() {
    echo "Starting application build"
    withCredentials([file(credentialsId: 'jenkins-gcr-account', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
        sh 'docker login -u _json_key -p "`cat ${GOOGLE_APPLICATION_CREDENTIALS}`" https://gcr.io'
        sh 'docker build -f backend/core/Dockerfile backend/core/ -t backend'
        sh 'docker tag backend gcr.io/mima-325516/texas/backend:prod'
        sh 'docker tag backend gcr.io/mima-325516/texas/worker:prod'
    }
    echo "Image pushed to AWS"
}

def PushImagetgoDev() {
    echo "Push Tested image to repo"
    withCredentials([file(credentialsId: 'jenkins-gcr-account', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
        sh 'docker login -u _json_key -p "`cat ${GOOGLE_APPLICATION_CREDENTIALS}`" https://gcr.io'
        sh 'docker push gcr.io/mima-325516/texas/worker:dev'
        sh 'docker push gcr.io/mima-325516/texas/backend:dev'
    }
    echo "Image pushed to Google container registry"
}

def PushImagetgoProd() {
    echo "Push Tested image to repo"
    withCredentials([file(credentialsId: 'jenkins-gcr-account', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
        sh 'docker login -u _json_key -p "`cat ${GOOGLE_APPLICATION_CREDENTIALS}`" https://gcr.io'
        sh 'docker push gcr.io/mima-325516/texas/worker:prod'
        sh 'docker push gcr.io/mima-325516/texas/backend:prod'
    }
    echo "Image pushed to Google container registry"
}

def TestApp() {
    echo "Starting unit  test"
    sh 'cp .env.prod .env.dev'
    sh 'docker-compose -f docker-compose.yml up -d && docker-compose -f docker-compose.yml exec -T backend python -m pytest -v && docker-compose -f docker-compose.yml down'
}

def deployToDev() {
    sh 'echo "starting deployment"'
    sh 'cd /opt/configuration/charts/ && /usr/local/bin/helm upgrade \
    --install  --wait --atomic worker mima_texas \
    --values /opt/configuration/dev/values-worker.yaml \
    --set image.releaseDate=VRSN`date +%Y%m%d-%H%M%S` --set image.tag=dev \
    -n dev'
    sh 'cd /opt/configuration/charts/ && /usr/local/bin/helm upgrade \
    --install backend backend \
    --values /opt/configuration/dev/values-backend.yaml \
    --set image.releaseDate=VRSN`date +%Y%m%d-%H%M%S` --set image.tag=dev \
    -n dev'
    echo "Core app deployed to dev env"
}



def DeployToProd() {
    sh 'echo "starting deployment"'
    sh 'cd /opt/configuration/charts/'
    sh 'cd /opt/configuration/charts/ && /usr/local/bin/helm upgrade \
    --install  --wait --atomic worker mima_texas \
    --values /opt/configuration/prod/values-worker.yaml \
    --set image.releaseDate=VRSN`date +%Y%m%d-%H%M%S` --set image.tag=prod \
    -n prod'
    sh 'cd /opt/configuration/charts/ && /usr/local/bin/helm upgrade \
    --install backend backend \
    --values /opt/configuration/prod/values-backend.yaml \
    --set image.releaseDate=VRSN`date +%Y%m%d-%H%M%S` --set image.tag=prod \
    -n prod'
    echo "Core app deployed to prod"
}

return this
