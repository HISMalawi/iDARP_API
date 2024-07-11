pipeline {
  agent {
    docker {
      image 'data_dict'
    }

  }
  stages {
    stage('Run Locally') {
      steps {
        sh 'sudo docker run -d -p 8000:8000 --name data_dict_con data_dict'
      }
    }

    stage('Test') {
      steps {
        echo 'Its Runnning'
      }
    }

  }
}