# S3 Component Replacer

A Python CLI tool for copying versioned component files between S3 path prefixes (e.g., `dev/` → `stage/` → `prd/`). Designed for automated component deployment across environments.

## 1. Project Overview

This tool automates the promotion of versioned component files between S3 prefixes within the same bucket. It extracts version numbers from component names, matches them to JSON configurations, and copies files using AWS S3 operations.

**Use Cases:**
- Promote components from `dev/` to `stage/` for QA
- Deploy components from `stage/` to `prd/` for production
- Copy between any custom S3 path prefixes

## 2. Key Features

- **Version Extraction**: Automatically extracts version numbers (1-3+ digits) from component names
- **JSON Configuration**: Component mappings and target lists defined in JSON files
- **Flexible Prefixes**: Configurable source/destination prefixes (`dev`, `stage`, `prd`, etc.)
- **AWS SSO Support**: Seamless integration with AWS Single Sign-On profiles
- **Auto Region Detection**: Automatically detects S3 bucket region
- **Dry-Run Mode**: Test operations without making S3 changes
- **Efficient Permissions**: Uses `list_objects_v2` for file checks (only needs `s3:ListBucket`)
- **Docker Support**: Containerized deployment for consistent execution

## 3. Quick Start

### Docker

```bash
# Build image
docker build -t s3-component-replacer .

# Run with AWS SSO profile
docker run --rm \
  -v $HOME/.aws:/home/appuser/.aws:ro \
  s3-component-replacer \
  --profile your-profile-name \
  --dry-run

# Run with environment variables
docker run --rm \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  s3-component-replacer \
  --dry-run
```

### Local Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS SSO (recommended)
aws configure sso --profile your-profile-name
aws sso login --profile your-profile-name

# Run script
python src/s3_component_replacer.py --profile your-profile-name --dry-run
```

## 4. Usage Examples

### Basic Operations

```bash
# Dry-run (test without changes)
python src/s3_component_replacer.py --profile xyz --dry-run

# Copy dev → stage (default)
python src/s3_component_replacer.py --profile xyz

# Copy stage → prd
python src/s3_component_replacer.py \
  --profile xyz \
  --source-prefix stage \
  --destination-prefix prd

# Custom bucket and config files
python src/s3_component_replacer.py \
  --profile xyz \
  --bucket my-bucket \
  --mapping-file config/custom_mapping.json \
  --components-file config/custom_components.json

# Debug mode
python src/s3_component_replacer.py \
  --profile xyz \
  --log-level DEBUG \
  --dry-run
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--bucket` | S3 bucket name | `spinomenal-cdn-main` |
| `--source-prefix` | Source path prefix | `dev` |
| `--destination-prefix` | Destination path prefix | `stage` |
| `--profile` | AWS profile name | Default credential chain |
| `--mapping-file` | Component mappings JSON | `config/components_mapping.json` |
| `--components-file` | Component names JSON | `config/components_to_replace.json` |
| `--region` | AWS region | Auto-detect |
| `--log-level` | Logging level | `INFO` |
| `--dry-run` | Test mode | `False` |

## 5. Configuration Files

### `config/components_mapping.json`

Defines component type configurations:

```json
[
  {
    "component_key": "KP-SlotMachine-V2",
    "file_name_pattern": "slotmachine.{version}.min.js",
    "path": "krembo/krembo_componentsV2/game_type/slotmachine/"
  },
  {
    "component_key": "Component-A-V1",
    "file_name_pattern": "component-a.{version}.min.js",
    "path": "components/component-a/"
  }
]
```

**Fields:**
- `component_key`: Base name without version (for matching)
- `file_name_pattern`: Template with `{version}` placeholder
- `path`: Base S3 path (without prefix)

### `config/components_to_replace.json`

Lists components to process (with versions):

```json
[
  "KP-SlotMachine-V2-22",
  "Component-A-V1-19",
  "Component-B-227"
]
```

**Processing Example:**
- Component: `KP-SlotMachine-V2-22`
- Extracts version: `22`
- Matches: `component_key` = `"KP-SlotMachine-V2"`
- File name: `slotmachine.22.min.js`
- Source: `dev/krembo/.../slotmachine.22.min.js`
- Destination: `stage/krembo/.../slotmachine.22.min.js`

## 6. Requirements

### Python
- Python 3.7+
- Dependencies: `boto3`, `botocore`

### AWS Permissions

Required IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::bucket-name"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::bucket-name/*"
    }
  ]
}
```

**Permission Notes:**
- `s3:ListBucket`: For file existence checks
- `s3:GetObject`: For reading source files
- `s3:PutObject`: For writing destination files

## 7. Project Structure

```
s3-replacer/
├── src/
│   └── s3_component_replacer.py    # Main application
├── config/
│   ├── components_mapping.json      # Component configurations
│   └── components_to_replace.json  # Components to process
├── tests/
│   ├── test_aws_s3_access.py       # AWS integration tests
│   └── test_s3_component_replacer.py  # Unit tests
├── Dockerfile                       # Docker image definition
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 8. Troubleshooting

### Permission Denied (403)
- Verify IAM permissions (`s3:ListBucket`, `s3:GetObject`, `s3:PutObject`)
- Check AWS SSO login: `aws sso login --profile your-profile-name`
- Verify session token hasn't expired

### File Not Found (404)
- Check component name and version in `components_to_replace.json`
- Verify file exists in source prefix
- Ensure `file_name_pattern` matches actual file naming

### Configuration File Not Found
- Ensure files are in `config/` directory
- Run from project root: `cd s3-replacer && python src/s3_component_replacer.py`
- Use absolute paths if needed: `--mapping-file /path/to/file.json`



