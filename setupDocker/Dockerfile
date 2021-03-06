FROM centos

RUN echo "multilib_policy=best" >> /etc/yum.conf
RUN yum  -y update && \
	yum install -y gcc-c++ git xinetd perl curl python openssh-server openssh-clients expect man python-argparse sshpass wget make cmake dos2unix which unzip lsof net-tools|| true && \
	yum install -y http://libslack.org/daemon/download/daemon-0.6.4-1.i686.rpm > /dev/null && \
	package-cleanup --cleandupes && \
	yum  -y clean all

RUN ssh-keygen -f /etc/ssh/ssh_host_rsa_key -N '' -t rsa && \
    ssh-keygen -f /etc/ssh/ssh_host_dsa_key -N '' -t dsa && \
    ssh-keygen -t ecdsa -N "" -f /etc/ssh/ssh_host_ecdsa_key && \
    ssh-keygen -t ed25519 -N "" -f /etc/ssh/ssh_host_ed25519_key && \
    sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
	sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && \
	echo 'root:docker' | chpasswd

# Install node globally (4.* compatible with nodem)
# or https://gist.github.com/remarkablemark/aacf14c29b3f01d6900d13137b21db3a
RUN curl --silent --location https://rpm.nodesource.com/setup_4.x | bash -
RUN yum install -y nodejs > /dev/null
RUN npm install pm2 -g

WORKDIR /opt/vista
ADD . /opt/vista/

#
# nodeVISTA 
# - args: -b (docker) gtm (-g) p/s dev dirs (-d) skip tests (-s) named (-i). Expose 9000, 9011, 9012 too
# ... used -g along with older GTM/install.sh as version from 3/22/18 failed to install mumps (-y or -g)
# - ports: 9430 for RPC Broker, 9000 for FMQL
# ... note: not exposing 22 as can ssh using -exec -it --privileged <cid> bash
# 
RUN ./autoInstaller.sh -b -g -d -s -i nodevista && ./nodeVistaOverlay.sh
# original was /home/nodevista/bin/start.sh
ENTRYPOINT /home/nodevista/bin/entryCombo.sh
EXPOSE 9430 9000

