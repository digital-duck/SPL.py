# conda create -n spl123 python=3.11

conda activate spl123

cd ~/projects/digital-duck/SPL.py
pip install -e .

export MOMAGRID_HUB_URL=http://192.168.0.184:9000

# sanity test
spl3 run scripts/ollama_proxy.spl --adapter momagrid --model gemma3 \
    --param prompt="What is 10!"

# submit the full run_all.py script

## using spl3
# nohup 
python cookbook/run_all.py --adapter momagrid --model gemma3 --workers 10 \
    2>&1 | tee cookbook/logs/run_all_momagrid-spl3-$(date +%Y%m%d_%H%M%S).md  &


nohup python cookbook/run_all.py --adapter momagrid --model gemma3 --workers 10 \
    > cookbook/logs/run_all_momagrid-spl3-$(date +%Y%m%d_%H%M%S).md 2>&1 & 
echo $!
# 152955

## using spl-go
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json \
    --adapter momagrid --model gemma3 --workers 10 \
    2>&1 | tee cookbook/logs/run_all_momagrid-spl-go-$(date +%Y%m%d_%H%M%S).md  &


## using spl-ts
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-ts.json \
    --adapter momagrid --model gemma3 --workers 10 \
    2>&1 | tee cookbook/logs/run_all_momagrid-spl-ts-$(date +%Y%m%d_%H%M%S).md  &