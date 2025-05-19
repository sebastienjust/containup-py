set -e

echo "       ▗   ▘       "
echo " ▛▘▛▌▛▌▜▘▀▌▌▛▌▌▌▛▌ "
echo " ▙▖▙▌▌▌▐▖█▌▌▌▌▙▌▙▌ "
echo "                ▌  "

echo "🔍 Checking requirements..."

command -v python3 >/dev/null 2>&1 || { echo >&2 "❌ Python 3.9+ required."; exit 1; }

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED="3.9"

# Python version
if [ "$(printf '%s\n' "$REQUIRED" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
  echo "❌ Python >= 3.9 is required. Found: $PYTHON_VERSION"; exit 1
else
  echo "✅ Found Python $PYTHON_VERSION."
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "⚠️  Docker not found. Some features may not work."
else
  echo "✅ Docker is installed"

  if ! docker info >/dev/null 2>&1; then
    echo "⚠️  Docker is installed but the daemon is not running. Some features may not work."
  else
    echo "✅ Docker daemon is running."
  fi
fi

tmpdir=$(mktemp -d)
if ! python3 -m venv "$tmpdir" > /dev/null 2>&1; then
  echo "❌ Python 'venv' module is missing."
  echo "   Containup itself doesn't require a virtual environment,"
  echo "   but this installer uses one to avoid polluting your system environment."
  echo "👉 On Debian/Ubuntu: sudo apt install python3-venv"
  echo "   (or: sudo apt install python3.10-venv if using Python 3.10)"
  rm -rf "$tmpdir"
  exit 1
else
  echo "✅ Python virtualenv available."
  rm -rf "$tmpdir"
fi

default_dir="containup-example"
read -r -p "Where do you want to install your first script? [$default_dir] " target_dir
target_dir=${target_dir:-$default_dir}
echo "$target_dir"

if [ -e "$target_dir" ]; then
  echo "❌ Directory '$target_dir' already exists. Choose another one."
  exit 1
fi

mkdir -p "$target_dir"
cd "$target_dir" || exit 1

echo "🐍 Creating virtualenv..."
python3 -m venv .venv
source .venv/bin/activate

echo "📦 Installing containup using pip..."
pip install --upgrade pip
pip install containup typing_extensions

echo "----------------------------------------"
echo "✅ READY !"
echo "----------------------------------------"
default_sample="Y"
read -r -p "📦 Download and run a report on a sample stack? [Y/n] " response
response=${response:-$default_sample}

if [[ "$response" =~ ^[Yy]$ ]]; then
  echo "Proceeding..."
  echo "----------------------------------------"
  echo "✅ Example stack (from samples/sample_odoo.py)"
  curl -sSL -o containup_stack.py https://raw.githubusercontent.com/sebastienjust/containup-py/main/samples/sample_odoo.py
  echo "   This is the output of : python3 containup_stack.py up --dry-run"
  echo "----------------------------------------"
  python3 containup_stack.py up --dry-run
  echo ""
fi

echo "----------------------------------------"
echo "End of example - your can run it now, for real, if you want"
echo "python3 containup_stack.py up"
echo "----------------------------------------"
echo "Directory $target_dir created"
if [[ "$response" =~ ^[Yy]$ ]]; then
echo "Sample file containup_stack.py added"
fi
echo ""
echo "What's next:"
echo " - open the directory   : cd $target_dir"
echo " - activate .venv       : source .venv/bin/activate"
echo " - edit your script     : nano containup_stack.py"
echo " - dry run your changes : python containup_stack.py up --dry-run"
echo " - run for real         : python containup_stack.py up"
echo " - stop everything      : python containup_stack.py down"
echo " - get help             : python containup_stack.py --help"
echo "----------------------------------------"
