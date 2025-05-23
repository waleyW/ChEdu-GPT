import os
import sys
import math
import torch
import argparse
import textwrap
import transformers
from peft import PeftModel
from transformers import GenerationConfig, TextStreamer
from llama_attn_replace import replace_llama_attn
print("Model version:", transformers.__version__)
print("Torch version:", torch.__version__)

PROMPT_DICT = {
    "prompt_no_input": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Response:"
    ),
    "prompt_no_input_llama2": (
        "<s>[INST] <<SYS>>\n"
        "As a chemistry education assistant, when students express confusion about chemical concepts, use the Socratic method to guide their thinking rather than providing direct answers. Ask questions that help students explore on their own.\n\n"
        "As a chemistry education assistant, based on the student's answer and previous dialogue history, continue using Socratic questioning to guide the student to think more deeply about this chemistry concept.\n"
        "<</SYS>> \n\n {instruction} [/INST]"
    ),
    "prompt_input_llama2": (
        "<s>[INST] <<SYS>>\n"
        "As a chemistry education assistant, when students express confusion about chemical concepts, use the Socratic method to guide their thinking rather than providing direct answers. Ask questions that help students explore on their own.\n\n"
        "As a chemistry education assistant, based on the student's answer and previous dialogue history, continue using Socratic questioning to guide the student to think more deeply about this chemistry concept.\n"
        "<</SYS>> \n\n {instruction} [/INST]"
     )
}

def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--material', type=str, default="")
    parser.add_argument('--question', type=str, default="")
    parser.add_argument('--base_model', type=str, default="/data1/pretrained-models/llama-7b-hf")
    parser.add_argument('--cache_dir', type=str, default="./cache")
    parser.add_argument('--context_size', type=int, default=-1, help='context size during fine-tuning')
    parser.add_argument('--flash_attn', type=bool, default=False, help='')
    parser.add_argument('--temperature', type=float, default=1, help='')
    parser.add_argument('--top_p', type=float, default=0.9, help='')
    parser.add_argument('--max_gen_len', type=int, default=30000, help='')
    args = parser.parse_args()
    return args

def read_txt_file(material_txt):
    if not material_txt.split(".")[-1]=='txt':
        raise ValueError("Only support txt or pdf file.")
    content = ""
    with open(material_txt) as f:
        for line in f.readlines():
            content += line
    return content

def build_generator(
    model, tokenizer, temperature=0.6, top_p=0.9, max_gen_len=4096, use_cache=True
):
    def response(prompt):
        print("Original prompt:", prompt)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        print("Tokenized prompt:", inputs)
        streamer = TextStreamer(tokenizer)
        print("Generation parameters:")
        print("Max new tokens:", max_gen_len)
        print("Temperature:", temperature)
        print("Top p:", top_p)

        output = model.generate(
            **inputs,
            max_new_tokens=max_gen_len,
            temperature=temperature,
            top_p=top_p,
            use_cache=use_cache,
            streamer=streamer,
        )
        print("Raw model output:", output)       
        out = tokenizer.decode(output[0], skip_special_tokens= False)
        print("Decoded output:", out)
        #out = out.split(prompt.lstrip("<s>"))[1].strip()
        return out

    return response

def main(args):
    if args.flash_attn:
        replace_llama_attn(inference=True)

    # Set RoPE scaling factor
    config = transformers.AutoConfig.from_pretrained(
        args.base_model,
        cache_dir=args.cache_dir,
    )

    orig_ctx_len = getattr(config, "max_position_embeddings", None)
    if orig_ctx_len and args.context_size > orig_ctx_len:
        scaling_factor = float(math.ceil(args.context_size / orig_ctx_len))
        config.rope_scaling = {"type": "linear", "factor": scaling_factor}

    # Load model and tokenizer
    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.base_model,
        config=config,
        cache_dir=args.cache_dir,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.resize_token_embeddings(32001)

    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.base_model,
        cache_dir=args.cache_dir,
        model_max_length=args.context_size if args.context_size > orig_ctx_len else orig_ctx_len,
        padding_side="right",
        use_fast=True,
    )

    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)
    respond = build_generator(model, tokenizer, temperature=args.temperature, top_p=args.top_p,
                              max_gen_len=args.max_gen_len, use_cache=True)

    #material = read_txt_file(args.material)
    prompt_no_input = PROMPT_DICT["prompt_no_input_llama2"]
    prompt = prompt_no_input.format_map({"instruction": args.question})

    output = respond(prompt=prompt)
if __name__ == "__main__":
    args = parse_config()
    main(args)
