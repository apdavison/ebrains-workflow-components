# Build stage with Spack pre-installed and ready to be used
FROM spack/ubuntu-jammy:develop as builder

# What we want to install and how we want to install it
# is specified in a manifest file (spack.yaml)
COPY ./spack.yaml /opt/spack-environment/spack.yaml

# Get the additional EBRAINS package definitions
# TODO: here we get the main branch, we may wish to use a release tag
RUN git clone https://gitlab.ebrains.eu/ri/tech-hub/platform/esd/ebrains-spack-builds.git /opt/ebrains-spack-builds

# Install the software, remove unnecessary deps
RUN cd /opt/spack-environment && spack repo add /opt/ebrains-spack-builds && spack env activate . && spack install --fail-fast && spack gc -y

# Strip all the binaries
RUN find -L /opt/views/view/* -type f -exec readlink -f '{}' \; | \
    xargs file -i | \
    grep 'charset=binary' | \
    grep 'x-executable\|x-archive\|x-sharedlib' | \
    awk -F: '{print $1}' | xargs strip

# Modifications to the environment that are necessary to run
RUN cd /opt/spack-environment && \
    spack env activate --sh -d . > activate.sh


# Bare OS image to run the installed executables
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y gfortran

COPY --from=builder /opt/spack-environment /opt/spack-environment
COPY --from=builder /opt/software /opt/software

# paths.view is a symlink, so copy the parent to avoid dereferencing and duplicating it
COPY --from=builder /opt/views /opt/views

RUN { \
      echo '#!/bin/sh' \
      && echo '.' /opt/spack-environment/activate.sh \
      && echo 'PATH="/usr/src/app:$PATH"' \
      && echo 'exec "$@"'; \
    } > /entrypoint.sh \
&& chmod a+x /entrypoint.sh \
&& ln -s /opt/views/view /opt/view

WORKDIR /usr/src/app
COPY butter_cli.py butter_cli.py
RUN chmod +x butter_cli.py
ENV PATH="/usr/src/app:$PATH"

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "/bin/bash" ]
