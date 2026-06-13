#!/bin/bash

# 设置并行任务数量（根据系统资源调整）
NUM_PARALLEL_TASKS=8  # 可以根据CPU核心数调整

# 设置输入和输出目录
INPUT_DIR="${INPUT_DIR:-/path/to/input_pdbs}"
OUTPUT_DIR="${OUTPUT_DIR:-/path/to/output_dir}"
LOG_DIR="$OUTPUT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 定义处理单个 PDB 文件的函数
process_pdb() {
    local pdb_id=$1
    local log_file="$LOG_DIR/${pdb_id}.log"
    local err_file="$LOG_DIR/${pdb_id}.err"
    
    echo "开始处理文件：${pdb_id}.pdb" > "$log_file"
    echo "时间：$(date)" >> "$log_file"
    
    # 执行预处理命令
    ./preprocess_pdb.sh \
        "$INPUT_DIR/${pdb_id}.pdb" \
        "${pdb_id}_A" \
        -o "$OUTPUT_DIR" >> "$log_file" 2>> "$err_file"
    
    local return_code=$?
    
    if [ $return_code -eq 0 ]; then
        echo "成功处理文件：${pdb_id}.pdb，输出至：$OUTPUT_DIR/${pdb_id}_A.ply" >> "$log_file"
    else
        echo "处理文件 ${pdb_id}.pdb 失败，返回码：$return_code" >> "$err_file"
    fi
    
    echo "完成时间：$(date)" >> "$log_file"
}

export -f process_pdb
export INPUT_DIR
export OUTPUT_DIR
export LOG_DIR

# 检查是否安装了 GNU Parallel
has_parallel=$(command -v parallel >/dev/null 2>&1 && echo "yes" || echo "no")

if [ "$has_parallel" = "yes" ]; then
    echo "使用 GNU Parallel 进行并行计算"
    
    # 使用 GNU Parallel 进行并行处理
    # 生成 PDB ID 列表并传递给 parallel
    seq 1 500 | parallel -j "$NUM_PARALLEL_TASKS" process_pdb {}
    
else
    echo "未安装 GNU Parallel，使用 Bash 内置并行方式"
    
    # 使用 Bash 内置的后台任务进行并行处理
    # 计数变量
    task_count=0
    
    # 循环处理 PDB 文件
    for i in {1..500}; do
        # 启动一个后台任务
        process_pdb "$i" &
        
        # 增加任务计数
        ((task_count++))
        
        # 如果达到最大并行任务数，等待所有任务完成
        if [ "$task_count" -ge "$NUM_PARALLEL_TASKS" ]; then
            wait  # 等待所有后台任务完成
            task_count=0
        fi
    done
    
    # 等待剩余的后台任务完成
    wait
fi

# 汇总日志信息
success_count=$(grep -l "成功处理文件" "$LOG_DIR"/*.log | wc -l)
fail_count=$(ls -l "$LOG_DIR"/*.err | grep -v "^-rw-r--r--  *0" | wc -l)

if [ -d "$LOG_DIR" ]; then
    echo "并行处理完成！"
    echo "成功处理的文件数：$success_count"
    echo "处理失败的文件数：$fail_count"
    echo "详细日志请查看：$LOG_DIR 目录"
else
    echo "并行处理完成！"
    echo "无法统计结果，请检查日志目录是否创建成功"
fi
