build:
	docker build -t dudevpn_bot_image .
run:
	docker run -it -d --env-file .env --restart=unless-stopped --name dudevpn_bot dudevpn_bot_image
stop:
	docker stop dudevpn_bot
attach:
	docker attach dudevpn_bot
dell:
	docker rm dudevpn_bot
	docker image remove w1nn3rpy/dudevpn_bot_image