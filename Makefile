build:
	docker build -t dudevpn_bot_image .
run:
	docker run -it -d --network my_network -v /var/run/docker.sock:/var/run/docker.sock --env-file .env --restart=unless-stopped --name dudevpn_bot dudevpn_bot_image
stop:
	docker stop dudevpn_bot
attach:
	docker attach dudevpn_bot
dell:
	docker rm dudevpn_bot
	docker image remove dudevpn_bot_image
update:
	make stop
	make dell
	make build
	make run