"""
OCR Service - AWS Textract integration for PDF text extraction
"""
import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR Service using AWS Textract
    
    Extracts text from PDF documents for AI analysis
    """
    
    def __init__(self):
        """Initialize AWS Textract client"""
        self.textract_client = boto3.client(
            'textract',
            region_name=settings.AWS_TEXTRACT_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY
        )
    
    async def extract_text_from_s3(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """
        Extract text from PDF stored in S3 using AWS Textract
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (file path)
        
        Returns:
            {
                'success': True/False,
                'text': 'Extracted text...',
                'raw_response': {...},  # Full Textract response
                'error': 'Error message if failed'
            }
        """
        try:
            logger.info(f"Starting Textract OCR for s3://{bucket}/{key}")
            
            # Call AWS Textract Detect Document Text
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            # Extract text from response
            extracted_text = self._parse_textract_response(response)
            
            logger.info(
                f"Textract OCR completed. Extracted {len(extracted_text)} characters"
            )
            
            return {
                'success': True,
                'text': extracted_text,
                'raw_response': response,
                'page_count': len([
                    block for block in response.get('Blocks', [])
                    if block.get('BlockType') == 'PAGE'
                ])
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Textract error: {error_code} - {error_message}")
            
            return {
                'success': False,
                'error': f"Textract error: {error_code} - {error_message}",
                'text': ''
            }
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }
    
    def _parse_textract_response(self, response: Dict) -> str:
        """
        Parse Textract response and extract all text in reading order
        
        Args:
            response: Raw Textract API response
        
        Returns:
            Extracted text as string
        """
        blocks = response.get('Blocks', [])
        
        # Extract lines of text in order
        lines = []
        for block in blocks:
            if block.get('BlockType') == 'LINE':
                text = block.get('Text', '')
                if text.strip():
                    lines.append(text)
        
        # Join lines with newlines
        return '\n'.join(lines)
    
    async def extract_structured_data(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """
        Extract structured data (key-value pairs, tables) from document
        Uses Textract AnalyzeDocument API for more advanced extraction
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
        
        Returns:
            {
                'success': True/False,
                'text': 'Full text',
                'key_values': {'Invoice Number': '12345', ...},
                'tables': [...],
                'error': 'Error message if failed'
            }
        """
        try:
            logger.info(f"Starting Textract Analyze for s3://{bucket}/{key}")
            
            # Call AWS Textract Analyze Document (more advanced)
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=['FORMS', 'TABLES']  # Extract forms and tables
            )
            
            # Parse response
            full_text = self._parse_textract_response(response)
            key_values = self._extract_key_values(response)
            tables = self._extract_tables(response)
            
            logger.info(
                f"Textract Analyze completed. Found {len(key_values)} key-value pairs, "
                f"{len(tables)} tables"
            )
            
            return {
                'success': True,
                'text': full_text,
                'key_values': key_values,
                'tables': tables,
                'raw_response': response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Textract Analyze error: {error_code} - {error_message}")
            
            return {
                'success': False,
                'error': f"Textract Analyze error: {error_code} - {error_message}",
                'text': '',
                'key_values': {},
                'tables': []
            }
        
        except Exception as e:
            logger.error(f"Structured extraction failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'key_values': {},
                'tables': []
            }
    
    def _extract_key_values(self, response: Dict) -> Dict[str, str]:
        """Extract key-value pairs from Textract response"""
        key_values = {}
        blocks = response.get('Blocks', [])
        
        # Build block map for relationship lookup
        block_map = {block['Id']: block for block in blocks}
        
        # Find KEY_VALUE_SET blocks
        for block in blocks:
            if block.get('BlockType') == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    key_text = self._get_text_from_relationship(block, block_map, 'CHILD')
                    value_block = self._get_value_block(block, block_map)
                    
                    if value_block:
                        value_text = self._get_text_from_relationship(
                            value_block, block_map, 'CHILD'
                        )
                        if key_text and value_text:
                            key_values[key_text.strip()] = value_text.strip()
        
        return key_values
    
    def _extract_tables(self, response: Dict) -> list:
        """Extract tables from Textract response"""
        # Simplified table extraction - can be enhanced
        tables = []
        blocks = response.get('Blocks', [])
        
        for block in blocks:
            if block.get('BlockType') == 'TABLE':
                tables.append({
                    'confidence': block.get('Confidence', 0),
                    'row_count': block.get('RowCount', 0),
                    'column_count': block.get('ColumnCount', 0)
                })
        
        return tables
    
    def _get_text_from_relationship(
        self,
        block: Dict,
        block_map: Dict,
        relationship_type: str
    ) -> str:
        """Helper to get text from related blocks"""
        text = ""
        relationships = block.get('Relationships', [])
        
        for relationship in relationships:
            if relationship['Type'] == relationship_type:
                for child_id in relationship.get('Ids', []):
                    child_block = block_map.get(child_id)
                    if child_block and child_block.get('BlockType') == 'WORD':
                        text += child_block.get('Text', '') + ' '
        
        return text.strip()
    
    def _get_value_block(self, key_block: Dict, block_map: Dict) -> Optional[Dict]:
        """Helper to get VALUE block from KEY block"""
        relationships = key_block.get('Relationships', [])
        
        for relationship in relationships:
            if relationship['Type'] == 'VALUE':
                value_ids = relationship.get('Ids', [])
                if value_ids:
                    return block_map.get(value_ids[0])
        
        return None
