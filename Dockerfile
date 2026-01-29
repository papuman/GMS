# Build Odoo 19 Enterprise from local source code
FROM debian:bookworm-slim

# Set environment variables
ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dirmngr \
    fonts-noto-cjk \
    gnupg \
    libssl-dev \
    node-less \
    npm \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-wheel \
    xz-utils \
    libpq-dev \
    libjpeg-dev \
    libldap2-dev \
    libsasl2-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf
RUN curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_arm64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Create odoo user
RUN useradd -ms /bin/bash odoo

# Copy Odoo source code (Enterprise)
COPY --chown=odoo:odoo ./odoo /opt/odoo

# Remove old/conflicting versions of custom modules from Enterprise addons
RUN rm -rf /opt/odoo/addons/l10n_cr_einvoice /opt/odoo/addons/payment_tilopay

# Copy custom modules to dedicated custom_addons directory
COPY --chown=odoo:odoo ./l10n_cr_einvoice /opt/odoo/custom_addons/l10n_cr_einvoice
COPY --chown=odoo:odoo ./payment_tilopay /opt/odoo/custom_addons/payment_tilopay

# Install Odoo Python dependencies
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Install custom module dependencies (compatible with Python 3.11)
RUN pip3 install --no-cache-dir --break-system-packages \
    xmlschema==3.0.1 \
    cryptography==3.4.8 \
    pyOpenSSL==21.0.0

# Set permissions
RUN mkdir -p /var/lib/odoo /mnt/extra-addons \
    && chown -R odoo:odoo /opt/odoo /var/lib/odoo /mnt/extra-addons

# Copy entrypoint script
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Switch to odoo user
USER odoo

# Expose Odoo port
EXPOSE 8069

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
