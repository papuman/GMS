# -*- coding: utf-8 -*-
import base64
import io
import logging

try:
    import qrcode
    from qrcode.image.pil import PilImage
except ImportError:
    qrcode = None

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QRGenerator(models.AbstractModel):
    """
    QR Code generator for Costa Rica electronic invoices.

    Generates QR codes according to Hacienda specifications:
    - URL format: https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/facturaElectronica.html?clave={clave}
    - Size: 150x150 pixels minimum
    - Error correction: HIGH level
    - Output: Base64 encoded PNG for embedding in PDF
    """
    _name = 'l10n_cr.qr.generator'
    _description = 'Costa Rica E-Invoice QR Code Generator'

    @api.model
    def generate_qr_code(self, clave):
        """
        Generate QR code for electronic invoice clave.

        Args:
            clave (str): 50-digit Hacienda key (clave)

        Returns:
            str: Base64 encoded PNG image

        Raises:
            UserError: If qrcode library is not available or generation fails
        """
        if not qrcode:
            raise UserError(_(
                'QR code library is not installed. '
                'Please install it using: pip install qrcode[pil]'
            ))

        if not clave or len(clave) != 50:
            raise UserError(_(
                'Invalid clave format. Expected 50 digits, got: %s'
            ) % (len(clave) if clave else 0))

        try:
            # Build Hacienda validation URL
            url = self._build_hacienda_url(clave)

            # Generate QR code with HIGH error correction
            qr = qrcode.QRCode(
                version=None,  # Auto-determine version based on data
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # HIGH level
                box_size=10,  # Size of each box in pixels
                border=4,  # Minimum border size (4 boxes)
            )

            qr.add_data(url)
            qr.make(fit=True)

            # Create PIL image (black and white)
            img = qr.make_image(fill_color="black", back_color="white")

            # Ensure minimum size of 150x150
            img_size = img.size[0]
            if img_size < 150:
                # Calculate scaling factor to reach 150px minimum
                scale = int(150 / img_size) + 1
                new_size = img_size * scale
                img = img.resize((new_size, new_size))

            # Convert to base64
            base64_img = self._image_to_base64(img)

            _logger.info(f'Generated QR code for clave: {clave[:20]}...')

            return base64_img

        except Exception as e:
            _logger.error(f'Error generating QR code: {str(e)}')
            raise UserError(_(
                'Error generating QR code: %s'
            ) % str(e))

    @api.model
    def _build_hacienda_url(self, clave):
        """
        Build the Hacienda validation URL with clave parameter.

        Args:
            clave (str): 50-digit Hacienda key

        Returns:
            str: Complete URL for QR code
        """
        # Use Tribunet Hacienda validation page
        base_url = 'https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/facturaElectronica.html'
        return f'{base_url}?clave={clave}'

    @api.model
    def _image_to_base64(self, pil_image):
        """
        Convert PIL image to base64 string.

        Args:
            pil_image: PIL Image object

        Returns:
            str: Base64 encoded PNG image
        """
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')

    @api.model
    def generate_qr_code_for_document(self, document):
        """
        Generate QR code for an einvoice document.

        Convenience method that takes a document record and generates
        its QR code.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            str: Base64 encoded PNG image

        Raises:
            UserError: If document has no clave
        """
        if not document.clave:
            raise UserError(_(
                'Cannot generate QR code: Document %s has no clave'
            ) % document.name)

        return self.generate_qr_code(document.clave)
