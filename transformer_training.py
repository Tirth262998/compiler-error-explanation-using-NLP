"""
Transformer Model Training Pipeline
Fine-tune CodeBERT/T5 for compiler error explanation generation
"""

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,
    T5ForConditionalGeneration,
    T5Tokenizer,
    get_linear_schedule_with_warmup
)
import json
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from tqdm import tqdm
import os

@dataclass
class TrainingConfig:
    model_name: str = "Salesforce/codet5-base"
    max_input_length: int = 512
    max_target_length: int = 256
    batch_size: int = 8
    learning_rate: float = 3e-5
    num_epochs: int = 10
    warmup_steps: int = 500
    gradient_accumulation_steps: int = 4
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    output_dir: str = "./models/compiler_explainer"

class CompilerErrorDataset(Dataset):
    """Dataset for compiler error -> explanation pairs"""
    
    def __init__(self, data_path: str, tokenizer, max_input_len: int, max_target_len: int):
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_target_len = max_target_len
        self.examples = self._load_data(data_path)
    
    def _load_data(self, data_path: str) -> List[Dict]:
        """Load training data from JSON file"""
        with open(data_path, 'r') as f:
            data = json.load(f)
        return data
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Construct input: error message + code context
        input_text = self._format_input(example)
        target_text = self._format_target(example)
        
        # Tokenize
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_input_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        target_encoding = self.tokenizer(
            target_text,
            max_length=self.max_target_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        labels = target_encoding['input_ids'].squeeze(0)
        labels[labels == self.tokenizer.pad_token_id] = -100
        
        return {
            'input_ids': input_encoding['input_ids'].squeeze(0),
            'attention_mask': input_encoding['attention_mask'].squeeze(0),
            'labels': labels
        }
    
    def _format_input(self, example: Dict) -> str:
        """Format input for the model"""
        parts = [
            f"Error: {example['error_message']}",
            f"Type: {example['error_type']}",
            f"Code: {example['code_snippet']}",
        ]
        
        if 'context' in example:
            parts.append(f"Context: {example['context']}")
        
        return " | ".join(parts)
    
    def _format_target(self, example: Dict) -> str:
        """Format target explanation"""
        explanation = example.get('explanation', {})
        
        parts = [
            f"Description: {explanation.get('description', '')}",
            f"Root Cause: {explanation.get('root_cause', '')}",
            f"Fix: {explanation.get('fix', '')}"
        ]
        
        return " | ".join(parts)

class CompilerExplainerTrainer:
    """Trainer for compiler error explanation model"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device(config.device)
        
        # Initialize tokenizer and model with cache-first / offline fallback
        self.tokenizer, self.model = self._load_model(config.model_name)
        self.model.to(self.device)
        
        # Training state
        self.best_loss = float('inf')
        self.global_step = 0
    
    @staticmethod
    def _load_model(model_name: str):
        """Load tokenizer and model with safety checks for meta tensors."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Load normally, completely avoiding 'device_map' and 'low_cpu_mem_usage'
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                # Verify no meta tensors are present
                if any(p.is_meta for p in model.parameters()):
                    print(f"[ERROR] Model loaded incorrectly (meta tensors detected) on attempt {attempt + 1}")
                    continue
                
                print("[OK] Model loaded successfully")
                return tokenizer, model
            except Exception as e:
                print(f"[ERROR] Loading failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Could not load model '{model_name}' successfully. Original error: {e}") from e
    
    def prepare_data(self, train_path: str, val_path: str = None):
        """Prepare training and validation datasets"""
        self.train_dataset = CompilerErrorDataset(
            train_path,
            self.tokenizer,
            self.config.max_input_length,
            self.config.max_target_length
        )
        
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        
        if val_path:
            self.val_dataset = CompilerErrorDataset(
                val_path,
                self.tokenizer,
                self.config.max_input_length,
                self.config.max_target_length
            )
            
            self.val_loader = DataLoader(
                self.val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=4,
                pin_memory=True
            )
        else:
            self.val_loader = None
    
    def setup_optimizer(self):
        """Setup optimizer and learning rate scheduler"""
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {
                'params': [p for n, p in self.model.named_parameters() 
                          if not any(nd in n for nd in no_decay)],
                'weight_decay': 0.01
            },
            {
                'params': [p for n, p in self.model.named_parameters() 
                          if any(nd in n for nd in no_decay)],
                'weight_decay': 0.0
            }
        ]
        
        self.optimizer = AdamW(
            optimizer_grouped_parameters,
            lr=self.config.learning_rate,
            eps=1e-8
        )
        
        total_steps = (len(self.train_loader) // self.config.gradient_accumulation_steps + (1 if len(self.train_loader) % self.config.gradient_accumulation_steps != 0 else 0)) * self.config.num_epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=total_steps
        )
    
    def train_epoch(self, epoch: int):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        
        progress_bar = tqdm(self.train_loader, desc=f"Epoch {epoch}")
        
        for step, batch in enumerate(progress_bar):
            # Move batch to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            loss = loss / self.config.gradient_accumulation_steps
            
            # Backward pass
            loss.backward()
            
            # Update weights
            if (step + 1) % self.config.gradient_accumulation_steps == 0 or (step + 1) == len(self.train_loader):
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad()
                self.global_step += 1
            
            total_loss += loss.item() * self.config.gradient_accumulation_steps
            
            # Update progress bar
            progress_bar.set_postfix({
                'loss': total_loss / (step + 1),
                'lr': self.scheduler.get_last_lr()[0]
            })
        
        return total_loss / len(self.train_loader)
    
    def validate(self):
        """Validate the model"""
        if self.val_loader is None:
            return None
        
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validation"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                total_loss += outputs.loss.item()
        
        return total_loss / len(self.val_loader)
    
    def train(self):
        """Main training loop"""
        print(f"Training on {self.device}")
        print(f"Number of training examples: {len(self.train_dataset)}")
        if self.val_loader:
            print(f"Number of validation examples: {len(self.val_dataset)}")
        
        self.setup_optimizer()
        
        for epoch in range(1, self.config.num_epochs + 1):
            print(f"\n{'='*60}")
            print(f"Epoch {epoch}/{self.config.num_epochs}")
            print(f"{'='*60}")
            
            # Train
            train_loss = self.train_epoch(epoch)
            print(f"Training Loss: {train_loss:.4f}")
            
            # Validate
            if self.val_loader:
                val_loss = self.validate()
                print(f"Validation Loss: {val_loss:.4f}")
                
                # Save best model
                if val_loss < self.best_loss:
                    self.best_loss = val_loss
                    self.save_model(f"best_model_epoch_{epoch}")
                    print(f"✓ New best model saved (loss: {val_loss:.4f})")
            
            # Save checkpoint
            if epoch % 2 == 0:
                self.save_model(f"checkpoint_epoch_{epoch}")
        
        print("\nTraining completed!")
    
    def save_model(self, checkpoint_name: str):
        """Save model checkpoint"""
        output_path = os.path.join(self.config.output_dir, checkpoint_name)
        os.makedirs(output_path, exist_ok=True)
        
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        # Save training config
        config_path = os.path.join(output_path, 'training_config.json')
        with open(config_path, 'w') as f:
            json.dump(vars(self.config), f, indent=2)
    
    def generate_explanation(self, error_message: str, code_snippet: str, 
                           error_type: str = "unknown") -> str:
        """Generate explanation for a given error"""
        self.model.eval()
        
        input_text = f"Error: {error_message} | Type: {error_type} | Code: {code_snippet}"
        
        input_ids = self.tokenizer(
            input_text,
            max_length=self.config.max_input_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        ).input_ids.to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                max_length=self.config.max_target_length,
                num_beams=4,
                early_stopping=True,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return explanation

class ModelEvaluator:
    """Evaluate model performance using BLEU and ROUGE metrics"""
    
    def __init__(self, model_path: str):
        self.tokenizer, self.model = CompilerExplainerTrainer._load_model(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
    
    def calculate_bleu(self, references: List[str], hypotheses: List[str]) -> float:
        """Calculate BLEU score (simplified)"""
        from collections import Counter
        
        total_score = 0
        for ref, hyp in zip(references, hypotheses):
            ref_tokens = ref.lower().split()
            hyp_tokens = hyp.lower().split()
            
            # Calculate precision
            common = Counter(ref_tokens) & Counter(hyp_tokens)
            num_common = sum(common.values())
            
            if len(hyp_tokens) > 0:
                precision = num_common / len(hyp_tokens)
                total_score += precision
        
        return total_score / len(references) if references else 0.0
    
    def calculate_rouge_l(self, reference: str, hypothesis: str) -> float:
        """Calculate ROUGE-L score (simplified)"""
        ref_tokens = reference.lower().split()
        hyp_tokens = hypothesis.lower().split()
        
        # Find longest common subsequence
        lcs_length = self._lcs_length(ref_tokens, hyp_tokens)
        
        if len(ref_tokens) == 0 or len(hyp_tokens) == 0:
            return 0.0
        
        recall = lcs_length / len(ref_tokens)
        precision = lcs_length / len(hyp_tokens)
        
        if recall + precision == 0:
            return 0.0
        
        f1 = 2 * recall * precision / (recall + precision)
        return f1
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Calculate longest common subsequence length"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def evaluate_dataset(self, test_data_path: str) -> Dict[str, float]:
        """Evaluate model on test dataset"""
        with open(test_data_path, 'r') as f:
            test_data = json.load(f)
        
        references = []
        hypotheses = []
        
        print("Generating explanations...")
        for example in tqdm(test_data):
            error_type = example.get('error_type', 'unknown')
            input_text = f"Error: {example['error_message']} | Type: {error_type} | Code: {example['code_snippet']}"
            
            input_ids = self.tokenizer(
                input_text,
                max_length=512,
                truncation=True,
                return_tensors='pt'
            ).input_ids.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(input_ids, max_length=256)
            
            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            reference = example['explanation']['description']
            
            hypotheses.append(generated)
            references.append(reference)
        
        # Calculate metrics
        bleu_score = self.calculate_bleu(references, hypotheses)
        
        rouge_scores = [self.calculate_rouge_l(ref, hyp) 
                       for ref, hyp in zip(references, hypotheses)]
        rouge_l = np.mean(rouge_scores)
        
        return {
            'bleu': bleu_score,
            'rouge_l': rouge_l,
            'num_examples': len(test_data)
        }

# Example usage and data generation
if __name__ == "__main__":
    # Generate sample training data
    sample_data = [
        {
            "error_message": "expected ';' before '}' token",
            "error_type": "syntax",
            "code_snippet": "int x = 5\n}",
            "explanation": {
                "description": "You forgot to end the statement with a semicolon.",
                "root_cause": "Every statement in C must end with a semicolon.",
                "fix": "Add a semicolon after 'int x = 5'"
            }
        },
        {
            "error_message": "'count' was not declared in this scope",
            "error_type": "semantic",
            "code_snippet": "printf(\"%d\", count);",
            "explanation": {
                "description": "The variable 'count' has not been declared.",
                "root_cause": "You're using a variable that doesn't exist in the current scope.",
                "fix": "Declare 'count' before using it: int count = 0;"
            }
        }
    ]
    
    # Save sample data
    os.makedirs('data', exist_ok=True)
    with open('data/train.json', 'w') as f:
        json.dump(sample_data * 100, f, indent=2)  # Duplicate for demo
    
    # Training configuration
    config = TrainingConfig(
        batch_size=4,
        num_epochs=3,
        output_dir="./models/compiler_explainer"
    )
    
    # Initialize trainer
    try:
        trainer = CompilerExplainerTrainer(config)
    except RuntimeError as e:
        print(e)
        print("\nTo download the model manually, run:")
        print("  python download_model.py")
        raise SystemExit(1)
    
    # Prepare data
    trainer.prepare_data('data/train.json')
    
    # Train model
    print("Starting training...")
    trainer.train()  # Uncomment to actually train
    
    print("\nTo train the model, uncomment trainer.train() above")
    print("Training requires significant computational resources")