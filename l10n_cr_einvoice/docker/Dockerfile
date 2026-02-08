# Multi-stage Dockerfile for Odoo 19 with Costa Rica E-Invoicing Module
# Production-ready with security hardening and optimization

# Stage 1: Builder
FROM odoo:19 AS builder

USER root

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Production
FROM odoo:19

LABEL maintainer="GMS Development Team <dev@gms-cr.com>"
LABEL description="Odoo 19 with Costa Rica E-Invoicing Module (Tribu-CR v4.4)"
LABEL version="19.0.1.8.0"

USER root

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    python3-pip \
    curl \
    postgresql-client \
    # For SSL/TLS support
    ca-certificates \
    # For QR code and PDF generation
    libpng16-16 \
    libjpeg62-turbo \
    # For XML processing
    libxml2 \
    libxslt1.1 \
    # Security tools
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create directories for custom modules and data
RUN mkdir -p /mnt/extra-addons /var/lib/odoo/.local/share/Odoo/filestore \
    && chown -R odoo:odoo /mnt/extra-addons /var/lib/odoo

# Copy the e-invoicing module
COPY --chown=odoo:odoo . /mnt/extra-addons/l10n_cr_einvoice/

# Copy Odoo configuration
COPY --chown=odoo:odoo docker/odoo.conf /etc/odoo/

# Security: Remove unnecessary packages
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    apt-get clean

# Security: Set proper permissions
RUN chmod 755 /mnt/extra-addons && \
    chmod 640 /etc/odoo/odoo.conf && \
    chown odoo:odoo /etc/odoo/odoo.conf

# Switch to non-root user
USER odoo

# Set working directory
WORKDIR /var/lib/odoo

# Environment variables
ENV ODOO_RC=/etc/odoo/odoo.conf \
    PATH="/usr/local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8069/web/health || exit 1

# Expose Odoo ports
EXPOSE 8069 8072

# Volume mounts for persistent data
VOLUME ["/var/lib/odoo", "/mnt/extra-addons"]

# Default command
CMD ["odoo", "--config=/etc/odoo/odoo.conf"]
