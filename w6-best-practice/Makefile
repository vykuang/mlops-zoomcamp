LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H-%M-%S")
LOCAL_IMG_NAME:=stream-model-duration:${LOCAL_TAG}

# test_name:
# 	echo ${LOCAL_TAG} ${LOCAL_IMG_NAME}
# 	sleep 1
# 	echo ${LOCAL_IMG_NAME}
test:
	pytest tests/

quality_checks: integration_test
	isort .
	black .
	pylint .

build: quality_checks test
	docker build -t ${LOCAL_IMG_NAME} .

integration_test: build
# sets shell var for the run.sh script
	LOCAL_IMG_NAME=${LOCAL_IMG_NAME} bash integration-test/run.sh

publish: build
