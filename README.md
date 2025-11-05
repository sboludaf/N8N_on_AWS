# N8N on AWS ECS - CloudFormation Deployment

This repository contains a CloudFormation template to deploy N8N workflow automation tool on AWS ECS Fargate with persistent storage using EFS.

## Architecture Overview

The deployment creates:

- **VPC with public and private subnets** across 2 availability zones
- **EFS file system** for persistent N8N data storage (mounted in public subnets)
- **ECS Fargate cluster** running in public subnets (cost-optimized, no NAT Gateway)
- **Application Load Balancer** with optional SSL/TLS support
- **Security groups** with proper access controls
- **CloudWatch logs** for monitoring

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. A domain name (optional, for custom domain and SSL)
3. ACM certificate (optional, for HTTPS)
4. ECS Service Linked Role (will be created automatically if it doesn't exist)

### Create ECS Service Linked Role (if needed)

If you encounter issues with the ECS cluster creation, you may need to create the ECS service linked role manually:

```bash
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com
```

**Note**: This command will fail if the role already exists, which is normal.

## Quick Deployment

### Basic Deployment (HTTP only)

```bash
aws cloudformation create-stack \
  --stack-name n8n-deployment \
  --template-body file://n8n-ecs-cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=InstanceName,ParameterValue=production \
               ParameterKey=TaskCpu,ParameterValue=1024 \
               ParameterKey=TaskMemory,ParameterValue=3072
```

### Multiple Instance Deployment

Deploy multiple N8N instances without resource collisions:

```bash
# Production instance
aws cloudformation create-stack \
  --stack-name n8n-production \
  --template-body file://n8n-ecs-cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=InstanceName,ParameterValue=production

# Development instance  
aws cloudformation create-stack \
  --stack-name n8n-development \
  --template-body file://n8n-ecs-cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=InstanceName,ParameterValue=development

# Testing instance
aws cloudformation create-stack \
  --stack-name n8n-testing \
  --template-body file://n8n-ecs-cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=InstanceName,ParameterValue=testing
```

### Deployment with Custom Domain and SSL

1. **Create ACM Certificate** (if you don't have one):
   ```bash
   aws acm request-certificate \
     --domain-name your-domain.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Deploy with SSL**:
   ```bash
   aws cloudformation create-stack \
     --stack-name n8n-production \
     --template-body file://n8n-ecs-cloudformation.yaml \
     --capabilities CAPABILITY_IAM \
     --parameters ParameterKey=InstanceName,ParameterValue=production \
                  ParameterKey=DomainName,ParameterValue=n8n.your-domain.com \
                  ParameterKey=CertificateArn,ParameterValue=arn:aws:acm:region:account:certificate/cert-id \
                  ParameterKey=TaskCpu,ParameterValue=1024 \
                  ParameterKey=TaskMemory,ParameterValue=3072
   ```

## Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `InstanceName` | Unique name for this N8N instance | `default` | No |
| `DomainName` | Custom domain for N8N | Empty | No |
| `CertificateArn` | ACM Certificate ARN for HTTPS | Empty | No |
| `N8NImage` | N8N Docker image | `docker.n8n.io/n8nio/n8n:latest` | No |
| `TaskCpu` | CPU units (1024 = 1 vCPU) | 1024 | No |
| `TaskMemory` | Memory in MB | 3072 | No |

## Post-Deployment Steps

### 1. Access N8N

After deployment, get the load balancer URL:

```bash
aws cloudformation describe-stacks \
  --stack-name n8n-production \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
  --output text
```

### 2. Setup Custom Domain (Optional)

If using a custom domain, create a CNAME record pointing to the load balancer DNS:

```bash
# Get the load balancer DNS
aws cloudformation describe-stacks \
  --stack-name n8n-production \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
  --output text
```

Create a CNAME record in your DNS provider:
- **Name**: `n8n` (or your subdomain)
- **Type**: `CNAME`
- **Value**: `[LoadBalancer DNS from above]`

### 3. Initial N8N Setup

1. Open the N8N URL in your browser
2. Create your admin account
3. Configure your workflows

## Monitoring and Logs

View N8N logs in CloudWatch:

```bash
aws logs describe-log-groups --log-group-name-prefix "/ecs/n8n-production"
```

## Scaling

To scale the service:

```bash
aws ecs update-service \
  --cluster n8n-production-production-n8n-cluster \
  --service n8n-production-production-n8n-service \
  --desired-count 2
```

## Connecting to RDS (Optional)

To use PostgreSQL instead of SQLite:

1. Create an RDS PostgreSQL instance
2. Update the task definition with database environment variables:
   - `DB_TYPE=postgresdb`
   - `DB_POSTGRESDB_HOST=your-rds-endpoint`
   - `DB_POSTGRESDB_PORT=5432`
   - `DB_POSTGRESDB_DATABASE=n8n`
   - `DB_POSTGRESDB_USER=your-username`
   - `DB_POSTGRESDB_PASSWORD=your-password`

## Security Considerations

- **N8N runs in public subnets** but is protected by security groups that only allow traffic from the Load Balancer
- **EFS is encrypted** at rest and in transit
- **Security groups** follow least privilege principle - only necessary ports are open
- **No direct access** to N8N containers - all traffic goes through the Load Balancer
- **Use AWS Secrets Manager** for sensitive configuration
- **Consider using private subnets** with NAT Gateway for production environments requiring additional network isolation

## Cost Optimization

- **No NAT Gateway costs**: Saves ~$45/month per gateway by using public subnets
- **Use Fargate Spot** for non-critical workloads
- **Adjust CPU/Memory** based on actual usage
- **Consider using reserved capacity** for predictable workloads
- **Monitor CloudWatch metrics** for right-sizing
- **EFS Intelligent Tiering** automatically moves files to lower-cost storage classes

## Troubleshooting

### Service Won't Start

Check ECS service events:
```bash
aws ecs describe-services \
  --cluster n8n-production-production-n8n-cluster \
  --services n8n-production-production-n8n-service
```

### EFS Mount Issues

Verify security groups allow NFS traffic (port 2049) between ECS and EFS.

### SSL Certificate Issues

Ensure the certificate is validated and in the same region as the load balancer.

## Cleanup

To delete the entire deployment:

```bash
aws cloudformation delete-stack --stack-name n8n-production
```

**Note**: This will delete all data. Backup your N8N workflows before deletion.

## Support

Based on the deployment guide from: [How to Deploy n8n to AWS ECS](https://medium.com/@destiya.dian/how-to-deploy-n8n-to-aws-part-i-ecs-710742460128)

For issues, check:
- CloudFormation events in AWS Console
- ECS service logs in CloudWatch
- N8N documentation: https://docs.n8n.io/
