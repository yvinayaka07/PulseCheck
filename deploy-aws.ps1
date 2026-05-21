# =============================================================================
# PulseCheck – AWS ECS Fargate Deployment Automator (PowerShell)
# Usage: .\deploy-aws.ps1 [-Environment <development|staging|production>]
# =============================================================================

Param (
    [ValidateSet("development", "staging", "production")]
    [String]$Environment = "production",
    
    [String]$Region = "ap-south-1",
    [String]$Account = "758388042692",
    [String]$VpcId = "vpc-05750e1a785e9555d",
    [String]$SubnetIds = "subnet-0dd5031599be06581,subnet-05d510acad4f17a30,subnet-08a5b5cf3035b3dcd",
    [String]$RepositoryName = "pulsecheck"
)

$ErrorActionPreference = "Stop"

$RegistryUri = "$Account.dkr.ecr.$Region.amazonaws.com"
$ImageUri = "$RegistryUri/$RepositoryName:latest"
$StackName = "pulsecheck-$Environment"

Write-Host "====================================================" -ForegroundColor Green
Write-Host " 🩺 PulseCheck AWS ECS Fargate Deployment" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Region:      $Region" -ForegroundColor Cyan
Write-Host "Account ID:  $Account" -ForegroundColor Cyan
Write-Host "VPC ID:      $VpcId" -ForegroundColor Cyan
Write-Host "Subnets:     $SubnetIds" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""

# ── Step 1: Verify AWS CLI & Identity ─────────────────────────────────────────
Write-Host "[1/5] Verifying AWS CLI & credentials..." -ForegroundColor Cyan
$awsInstalled = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsInstalled) {
    Write-Host "❌ AWS CLI is not installed or not in system PATH." -ForegroundColor Red
    Write-Host "Please install the AWS CLI (https://aws.amazon.com/cli/) and try again." -ForegroundColor Yellow
    Exit 1
}

try {
    $identity = aws sts get-caller-identity --query "Arn" --output text --region $Region
    Write-Host "✅ Authenticated with IAM Identity: $identity" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS Authentication failed." -ForegroundColor Red
    Write-Host "Please run 'aws configure' to set up your credentials or check your connection." -ForegroundColor Yellow
    Exit 1
}
Write-Host ""

# ── Step 2: Verify & Wait for Docker ──────────────────────────────────────────
Write-Host "[2/5] Checking containerization environment..." -ForegroundColor Cyan

while ($true) {
    $dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerInstalled) {
        Write-Host "⚠️  Docker CLI is not recognized. Please install Docker Desktop." -ForegroundColor Yellow
        Write-Host "Make sure it is added to your PATH environment variable." -ForegroundColor Yellow
    } else {
        # Check if daemon is running
        & docker info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker environment is active and running." -ForegroundColor Green
            break
        }
        Write-Host "⚠️  Docker Desktop is installed, but the daemon is not running." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Press [Enter] to retry checking Docker, or press [Ctrl+C] to abort deployment." -ForegroundColor White
    Read-Host
}
Write-Host ""

# ── Step 3: Authenticate & Push Container Image to ECR ────────────────────────
Write-Host "[3/5] Building and pushing Docker container image..." -ForegroundColor Cyan

# ECR Login
Write-Host "Logging in to Amazon ECR registry ($RegistryUri)..." -ForegroundColor Gray
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $RegistryUri
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ECR Login failed!" -ForegroundColor Red
    Exit 1
}

# Docker build
Write-Host "Compiling production Docker container image..." -ForegroundColor Gray
docker build -t "$RepositoryName:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    Exit 1
}

# Tag image
Write-Host "Tagging image for ECR ($ImageUri)..." -ForegroundColor Gray
docker tag "$RepositoryName:latest" $ImageUri

# Push image
Write-Host "Uploading container image to ECR..." -ForegroundColor Gray
docker push $ImageUri
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push container image to ECR!" -ForegroundColor Red
    Exit 1
}

Write-Host "✅ Container image successfully pushed to AWS ECR!" -ForegroundColor Green
Write-Host ""

# ── Step 4: Deploy CloudFormation Stack ───────────────────────────────────────
Write-Host "[4/5] Deploying CloudFormation infrastructure stack ($StackName)..." -ForegroundColor Cyan
Write-Host "This process may take a few minutes as resources are provisioned on AWS..." -ForegroundColor Gray

try {
    aws cloudformation deploy `
      --stack-name $StackName `
      --template-file infrastructure/cloudformation.yml `
      --parameter-overrides `
        Environment=$Environment `
        ImageUri=$ImageUri `
        VpcId=$VpcId `
        SubnetIds=$SubnetIds `
      --capabilities CAPABILITY_NAMED_IAM `
      --region $Region
    
    Write-Host "✅ CloudFormation infrastructure stack deployed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ CloudFormation deployment failed!" -ForegroundColor Red
    Write-Host "Please check the AWS CloudFormation Console for detailed event logs." -ForegroundColor Yellow
    Exit 1
}
Write-Host ""

# ── Step 5: Retrieve Live URL ────────────────────────────────────────────────
Write-Host "[5/5] Retrieving application network configurations..." -ForegroundColor Cyan

$clusterName = "pulsecheck-cluster-$Environment"
$serviceName = "pulsecheck-service-$Environment"

# Wait a moment for service stabilization
Write-Host "Waiting for service tasks to stabilize and fetch networking details..." -ForegroundColor Gray
Start-Sleep -Seconds 10

try {
    $taskArn = aws ecs list-tasks --cluster $clusterName --service-name $serviceName --query "taskArns[0]" --output text --region $Region
    if ($taskArn -and $taskArn -ne "None") {
        $eniId = aws ecs describe-tasks --cluster $clusterName --tasks $taskArn --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text --region $Region
        if ($eniId -and $eniId -ne "None") {
            $publicIp = aws ec2 describe-network-interfaces --network-interface-ids $eniId --query "NetworkInterfaces[0].Association.PublicIp" --output text --region $Region
            if ($publicIp -and $publicIp -ne "None") {
                Write-Host "====================================================" -ForegroundColor Green
                Write-Host " 🎉 PulseCheck has been successfully deployed to AWS!" -ForegroundColor Green
                Write-Host "====================================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "🔗 Observability Dashboard: http://$publicIp:8000/" -ForegroundColor Green
                Write-Host "🔗 Health Status (JSON):   http://$publicIp:8000/health" -ForegroundColor Green
                Write-Host ""
                Write-Host "Note: Inbound security group allows direct access on port 8000." -ForegroundColor Gray
                Write-Host "====================================================" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Could not retrieve public IP. The task may still be provisioning." -ForegroundColor Yellow
                Write-Host "Use the AWS ECS Console to find the running task's IP or try running the script again in a minute." -ForegroundColor Yellow
            }
        } else {
            Write-Host "⚠️  Could not locate the Network Interface details for task: $taskArn" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  No running tasks found for ECS Service $serviceName yet." -ForegroundColor Yellow
        Write-Host "It might take another minute for AWS Fargate to start the container task." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Error retrieving task network details." -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
}
Write-Host ""
