INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/72_verify_arxiv_references/verify_arxiv_references.spl
Registry: ['verify_arxiv_references']
Running workflow: verify_arxiv_references(['in_refs', 'out_dir', 'model'])
INFO:httpx:HTTP Request: GET http://export.arxiv.org/api/query?id_list=2501.12948 "HTTP/1.1 301 Moved Permanently"
INFO:httpx:HTTP Request: GET https://export.arxiv.org/api/query?id_list=2501.12948 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (digest_writer) -> 115 tokens, 2729ms
INFO:spl.executor:GENERATE chain done -> @summary_desc (733 chars total)
INFO:spl.executor:RETURN: 54 chars | status=complete, total_refs=1, verified=1, skipped=0, skipped_csv_path=cookbook/72_verify_arxiv_references/output/summary-skipped.csv, log_file=/home/gongai/.spl/logs/verify_arxiv_references-20260721-000106.log
[INFO] Verify arXiv References — starting
[INFO] References parsed: 1
[INFO] Summary CSV: cookbook/72_verify_arxiv_references/output/summary.csv
[INFO] [0] arXiv:2501.12948 — looking up ground-truth record
[DEBUG] [0] downloaded -> cookbook/72_verify_arxiv_references/output/2501.12948.pdf
[INFO] [0] verified: "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning" (DeepSeek-AI; Daya Guo; Dejian Yang; Haowei Zhang; Junxiao Song; Peiyi Wang; Qihao Zhu; Runxin Xu; Ruoyu Zhang; Shirong Ma; Xiao Bi; Xiaokang Zhang; Xingkai Yu; Yu Wu; Z. F. Wu; Zhibin Gou; Zhihong Shao; Zhuoshu Li; Ziyi Gao; Aixin Liu; Bing Xue; Bingxuan Wang; Bochao Wu; Bei Feng; Chengda Lu; Chenggang Zhao; Chengqi Deng; Chenyu Zhang; Chong Ruan; Damai Dai; Deli Chen; Dongjie Ji; Erhang Li; Fangyun Lin; Fucong Dai; Fuli Luo; Guangbo Hao; Guanting Chen; Guowei Li; H. Zhang; Han Bao; Hanwei Xu; Haocheng Wang; Honghui Ding; Huajian Xin; Huazuo Gao; Hui Qu; Hui Li; Jianzhong Guo; Jiashi Li; Jiawei Wang; Jingchang Chen; Jingyang Yuan; Junjie Qiu; Junlong Li; J. L. Cai; Jiaqi Ni; Jian Liang; Jin Chen; Kai Dong; Kai Hu; Kaige Gao; Kang Guan; Kexin Huang; Kuai Yu; Lean Wang; Lecong Zhang; Liang Zhao; Litong Wang; Liyue Zhang; Lei Xu; Leyi Xia; Mingchuan Zhang; Minghua Zhang; Minghui Tang; Meng Li; Miaojun Wang; Mingming Li; Ning Tian; Panpan Huang; Peng Zhang; Qiancheng Wang; Qinyu Chen; Qiushi Du; Ruiqi Ge; Ruisong Zhang; Ruizhe Pan; Runji Wang; R. J. Chen; R. L. Jin; Ruyi Chen; Shanghao Lu; Shangyan Zhou; Shanhuang Chen; Shengfeng Ye; Shiyu Wang; Shuiping Yu; Shunfeng Zhou; Shuting Pan; S. S. Li; Shuang Zhou; Shaoqing Wu; Shengfeng Ye; Tao Yun; Tian Pei; Tianyu Sun; T. Wang; Wangding Zeng; Wanjia Zhao; Wen Liu; Wenfeng Liang; Wenjun Gao; Wenqin Yu; Wentao Zhang; W. L. Xiao; Wei An; Xiaodong Liu; Xiaohan Wang; Xiaokang Chen; Xiaotao Nie; Xin Cheng; Xin Liu; Xin Xie; Xingchao Liu; Xinyu Yang; Xinyuan Li; Xuecheng Su; Xuheng Lin; X. Q. Li; Xiangyue Jin; Xiaojin Shen; Xiaosha Chen; Xiaowen Sun; Xiaoxiang Wang; Xinnan Song; Xinyi Zhou; Xianzu Wang; Xinxia Shan; Y. K. Li; Y. Q. Wang; Y. X. Wei; Yang Zhang; Yanhong Xu; Yao Li; Yao Zhao; Yaofeng Sun; Yaohui Wang; Yi Yu; Yichao Zhang; Yifan Shi; Yiliang Xiong; Ying He; Yishi Piao; Yisong Wang; Yixuan Tan; Yiyang Ma; Yiyuan Liu; Yongqiang Guo; Yuan Ou; Yuduan Wang; Yue Gong; Yuheng Zou; Yujia He; Yunfan Xiong; Yuxiang Luo; Yuxiang You; Yuxuan Liu; Yuyang Zhou; Y. X. Zhu; Yanhong Xu; Yanping Huang; Yaohui Li; Yi Zheng; Yuchen Zhu; Yunxian Ma; Ying Tang; Yukun Zha; Yuting Yan; Z. Z. Ren; Zehui Ren; Zhangli Sha; Zhe Fu; Zhean Xu; Zhenda Xie; Zhengyan Zhang; Zhewen Hao; Zhicheng Ma; Zhigang Yan; Zhiyu Wu; Zihui Gu; Zijia Zhu; Zijun Liu; Zilin Li; Ziwei Xie; Ziyang Song; Zizheng Pan; Zhen Huang; Zhipeng Xu; Zhongyu Zhang; Zhen Zhang)
[INFO] Done — 1 verified / 0 skipped of 1 references. Summary: cookbook/72_verify_arxiv_references/output/summary.csv | Skipped: cookbook/72_verify_arxiv_references/output/summary-skipped.csv

Status:  complete
Output:  cookbook/72_verify_arxiv_references/output/summary.csv
LLM calls: 1  Latency: 2940ms
Log:     /home/gongai/.spl/logs/verify_arxiv_references-ollama-gemma3-20260721-000106.md
