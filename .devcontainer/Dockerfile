# 開発用コンテナなのでubuntuでええやろ
FROM ubuntu:22.04

# 開発環境に必要なパッケージなどはここでインストールしておきます
# gitはGitHub Codespacesで必須です
# curlも次のステップで使うので必須です
RUN apt update && apt install -y \
    git \
    curl \
    vim \
    htop \
    jq

# Docker from DockerするためにDockerをインストールします
RUN curl -fsSL https://get.docker.com | sh

EXPOSE 30000
EXPOSE 50000
EXPOSE 4317
EXPOSE 4442
EXPOSE 4443
EXPOSE 4444
EXPOSE 5901
EXPOSE 5902
EXPOSE 5903
EXPOSE 5904
EXPOSE 5905
EXPOSE 5906
EXPOSE 5907
EXPOSE 5908
EXPOSE 5909
EXPOSE 5910
EXPOSE 5911


# 実際に開発に使うroot以外のユーザーを作成します
RUN useradd -m user

# dockerコマンドを上記のroot以外のユーザーでも使えるようにするためにグチャグチャやってます
ARG NONROOT_USER=user
RUN echo "#!/bin/sh\n\
    sudoIf() { if [ \"\$(id -u)\" -ne 0 ]; then sudo \"\$@\"; else \"\$@\"; fi }\n\
    SOCKET_GID=\$(stat -c '%g' /var/run/docker.sock) \n\
    if [ \"${SOCKET_GID}\" != '0' ]; then\n\
        if [ \"\$(cat /etc/group | grep :\${SOCKET_GID}:)\" = '' ]; then sudoIf groupadd --gid \${SOCKET_GID} docker-host; fi \n\
        if [ \"\$(id ${NONROOT_USER} | grep -E \"groups=.*(=|,)\${SOCKET_GID}\(\")\" = '' ]; then sudoIf usermod -aG \${SOCKET_GID} ${NONROOT_USER}; fi\n\
    fi\n\
    exec \"\$@\"" > /usr/local/share/docker-init.sh \
    && chmod +x /usr/local/share/docker-init.sh

ENTRYPOINT [ "/usr/local/share/docker-init.sh" ]
CMD [ "sleep", "infinity" ]