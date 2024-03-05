#---------------#
# Builder image #
#---------------#
FROM postgres:latest AS BUILDER

# Install necessary dependencies for building PostgreSQL extensions and Python
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-server-dev-all \
    python3 \
    python3-pip \
    python3.11-venv

SHELL ["/bin/bash", "-c"]

RUN python3 -m venv venv
WORKDIR /venv/bin
RUN ./pip install pgxnclient
RUN ./pgxn install temporal_tables

#------------------#
# Production image #
#------------------#
FROM postgres:16-bullseye

RUN echo 'alias ll="ls -la"' >> ~/.bashrc

# Copy artefacts from BUILDER image
COPY --from=builder \
    /usr/lib/postgresql/16/lib/ \
    /usr/lib/postgresql/16/lib/
COPY --from=builder \
    /usr/share/postgresql/16/extension/ \
    /usr/share/postgresql/16/extension/
COPY --from=builder \
    /usr/share/postgresql/16/extension/ \
    /usr/share/postgresql/16/extension/
COPY --from=builder \
    /usr/share/doc/postgresql-doc-16/extension/ \
    /usr/share/doc/postgresql-doc-16/extension/

EXPOSE 5432

CMD ["postgres"]
