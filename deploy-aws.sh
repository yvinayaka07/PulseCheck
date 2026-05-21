#!/usr/bin/env bash
# =============================================================================
# PulseCheck – AWS ECS Fargate Deployment Automator (Bash)
# Usage: ./deploy-aws.sh [environment]
# =============================================================================

set -e

# Visual styling
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

ENVIRONMENT=${1:-"production"}
REGION="ap-south-1"
ACCOUNT="758388042692"
VPC_ID="vpc-05750e1a785e9555d"
SUBNET_IDS="subnet-0dd5031599be06581,subnet-05d510acad4f17a30,subnet-08a5b5cf3035b3dcd"
REPOSITORY_NAME="pulsecheck"

REGISTRY_URI="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
IMAGE_URI="$REGISTRY_URI/$REPOSITORY_NAME:latest"
STACK_NAME="pulsecheck-$ENVIRONMENT"

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN} 🩺 PulseCheck AWS ECS Fargate Deployment${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "${CYAN}Environment: $ENVIRONMENT${NC}"
echo -e "${CYAN}Region:      $REGION${NC}"
echo -e "${CYAN}Account ID:  $ACCOUNT${NC}"
echo -e "${CYAN}VPC ID:      $VPC_ID${NC}"
echo -e "${CYAN}Subnets:     $SUBNET_IDS${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""

# ── Step 1: Verify AWS CLI & Identity ─────────────────────────────────────────
echo -e "${CYAN}[1/5] Verifying AWS CLI & credentials...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed or not in system PATH.${NC}"
    echo -e "${YELLOW}Please install the AWS CLI (https://aws.amazon.com/cli/) and try again.${NC}"
    exit 1
fi

if identity=$(aws sts get-caller-identity --query "Arn" --output text --region "$REGION" 2>/dev/null); then
    echo -e "${GREEN}✅ Authenticated with IAM Identity: $identity${NC}"
else
    echo -e "${RED}❌ AWS Authentication failed.${NC}"
    echo -e "${YELLOW}Please run 'aws configure' to set up your credentials or check your connection.${NC}"
    exit 1
fi
echo ""

# ── Step 2: Verify & Wait for Docker ──────────────────────────────────────────
echo -e "${CYAN}[2/5] Checking containerization environment...${NC}"

while true; do
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker CLI is not recognized. Please install Docker.${NC}"
    else
        if docker info &> /dev/null; then
            echo -e "${GREEN}✅ Docker environment is active and running.${NC}"
            break
        fi
        echo -e "${YELLOW}⚠️  Docker is installed, but the daemon is not running.${NC}"
    fi

    echo ""
    read -p "Press [Enter] to retry checking Docker, or press [Ctrl+C] to abort deployment."
done
echo ""

# ── Step 3: Authenticate & Push Container Image to ECR ────────────────────────
echo -e "${CYAN}[3/5] Building and pushing Docker container image...${NC}"

# ECR Login
echo -e "${GRAY}Logging in to Amazon ECR registry ($REGISTRY_URI)...${NC}"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY_URI"

# Docker build
echo -e "${GRAY}Compiling production Docker container image...${NC}"
docker build -t "$REPOSITORY_NAME:latest" .

# Tag image
echo -e "${GRAY}Tagging image for ECR ($IMAGE_URI)...${NC}"
docker tag "$REPOSITORY_NAME:latest" "$IMAGE_URI"

# Push image
echo -e "${GRAY}Uploading container image to ECR...${NC}"
docker push "$IMAGE_URI"

echo -e "${GREEN}✅ Container image successfully pushed to AWS ECR!${NC}"
echo ""

# ── Step 4: Deploy CloudFormation Stack ───────────────────────────────────────
echo -e "${CYAN}[4/5] Deploying CloudFormation infrastructure stack ($STACK_NAME)...${NC}"
echo -e "${GRAY}This process may take a few minutes as resources are provisioned on AWS...${NC}"

if aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file infrastructure/cloudformation.yml \
  --parameter-overrides \
    Environment="$ENVIRONMENT" \
    ImageUri="$IMAGE_URI" \
    VpcId="$VPC_ID" \
    SubnetIds="$SUBNET_IDS" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION"; then
    echo -e "${GREEN}✅ CloudFormation infrastructure stack deployed successfully!${NC}"
else
    echo -e "${RED}❌ CloudFormation deployment failed!${NC}"
    echo -e "${YELLOW}Please check the AWS CloudFormation Console for detailed event logs.${NC}"
    exit 1
fi
echo ""

# ── Step 5: Retrieve Live URL ────────────────────────────────────────────────
echo -e "${CYAN}[5/5] Retrieving application network configurations...${NC}"

CLUSTER_NAME="pulsecheck-cluster-$ENVIRONMENT"
SERVICE_NAME="pulsecheck-service-$ENVIRONMENT"

# Wait a moment for service stabilization
echo -e "${GRAY}Waiting for service tasks to stabilize and fetch networking details...${NC}"
sleep 10

if task_arn=$(aws ecs list-tasks --cluster "$CLUSTER_NAME" --service-name "$SERVICE_NAME" --query "taskArns[0]" --output text --region "$REGION" 2>/dev/null); then
    if [ "$task_arn" != "None" ] && [ -n "$task_arn" ]; then
        if eni_id=$(aws ecs describe-tasks --cluster "$CLUSTER_NAME" --tasks "$task_arn" --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text --region "$REGION" 2>/dev/null); then
            if [ "$eni_id" != "None" ] && [ -n "$eni_id" ]; then
                if public_ip=$(aws ec2 describe-network-interfaces --network-interface-ids "$eni_id" --query "NetworkInterfaces[0].Association.PublicIp" --output text --region "$REGION" 2>/dev/null); then
                    if [ "$public_ip" != "None" ] && [ -n "$public_ip" ]; then
                        echo -e "${GREEN}====================================================${NC}"
                        echo -e "${GREEN} 🎉 PulseCheck has been successfully deployed to AWS!${NC}"
                        echo -e "${GREEN}====================================================${NC}"
                        echo ""
                        echo -e "${GREEN}🔗 Observability Dashboard: http://$public_ip:8000/${NC}"
                        echo -e "${GREEN}🔗 Health Status (JSON):   http://$public_ip:8000/health${NC}"
                        echo ""
                        echo -e "${GRAY}Note: Inbound security group allows direct access on port 8000.${NC}"
                        echo -e "${GREEN}====================================================${NC}"
                    else
                        echo -e "${YELLOW}⚠️  Could not retrieve public IP. The task may still be provisioning.${NC}"
                        echo -e "${YELLOW}Use the AWS ECS Console to find the running task's IP or try running the script again in a minute.${NC}"
                    fi
                fi
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  No running tasks found for ECS Service $SERVICE_NAME yet.${NC}"
        echo -e "${YELLOW}It might take another minute for AWS Fargate to start the container task.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Error retrieving task network details.${NC}"
fi
echo ""
