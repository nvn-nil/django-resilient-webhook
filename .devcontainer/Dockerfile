FROM windpioneers/gdal-python:modest-heron-gdal-2.4.1-python-3.9-dev


RUN curl -sSLo ./terraform-docs.tar.gz https://terraform-docs.io/dl/v0.17.0/terraform-docs-v0.17.0-$(uname)-amd64.tar.gz && \
    tar -xzf terraform-docs.tar.gz && \
    chmod +x terraform-docs && \
    mv terraform-docs /usr/bin/terraform-docs

# Install poetry
USER vscode
ENV POETRY_HOME=/home/vscode/.poetry
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH "$POETRY_HOME/bin:$PATH"
RUN poetry config virtualenvs.create false

# Install localtunnel
RUN npm install -g localtunnel
