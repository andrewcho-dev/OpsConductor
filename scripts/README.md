# Setup and Maintenance Scripts

This directory contains scripts for setting up and maintaining the OpsConductor platform.

## Setup Scripts

- `setup.sh` - Main setup script for initializing the platform
- `validate-setup.sh` - Validate the setup and configuration

## Database Scripts

- `alembic_safe.sh` - Safely run Alembic migrations
- `fix_alembic_permissions.sh` - Fix Alembic permission issues

## Maintenance Scripts

- `fix_datatables.sh` - Fix datatable issues

## Usage

These scripts should be run from the root directory:

```bash
cd /home/enabledrm
./scripts/setup.sh
```