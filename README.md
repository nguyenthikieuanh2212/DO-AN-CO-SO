## 1. Giới thiệu

Đồ án xây dựng pipeline gom cụm văn bản báo chí tiếng Việt theo hai hướng biểu diễn đặc trưng:

* **Lexical-based representation**: TF-IDF, BM25 kết hợp TruncatedSVD và K-Means.
* **Semantic-based representation**: Sentence embedding MiniLM kết hợp UMAP và K-Means.

Mục tiêu là so sánh hiệu quả giữa hướng lexical và semantic trong bài toán gom cụm văn bản báo chí, đồng thời khai thác FP-Max để hỗ trợ diễn giải đặc trưng nội dung của từng cụm.

## 2. Cấu trúc thư mục

```text
DO-AN-CO-SO/
├── src/
│   ├── 01_data_cleaning_eda.ipynb
│   ├── 02_vietnamese_text_preprocessing.ipynb
│   ├── 03_lexical_baselines_fpmax.ipynb
│   ├── 04_minilm_ablation_study.ipynb
│   ├── 05_minilm_fpmax_controlled_hybrid.ipynb
│   ├── 06_final_comparison_statistical_analysis.ipynb
│   └── tuoitre_scraper.py
├── README.md
└── .gitignore
```

Thư mục `data/` không được đưa trực tiếp lên GitHub do kích thước lớn. Dataset được lưu riêng trên Google Drive.

## 3. Dataset

Dataset gồm các bài báo tiếng Việt được thu thập từ báo Tuổi Trẻ theo 6 chuyên mục:

* Công nghệ
* Du lịch
* Giáo dục
* Sức khỏe
* Thể thao
* Xe

Link dataset: **[Dán link Google Drive dataset tại đây]**

## 4. Quy trình thực hiện

### Notebook 1: Data cleaning & EDA

Gộp dữ liệu từ các chuyên mục, kiểm tra dữ liệu thiếu, dữ liệu trùng, chuẩn hóa văn bản cơ bản và tạo bộ dữ liệu sạch ban đầu.

### Notebook 2: Vietnamese text preprocessing

Tạo các cột văn bản phục vụ gom cụm, bao gồm `cluster_text`, `cluster_text_clean`, `cluster_text_segmented` và `cluster_text_lexical`.

### Notebook 3: Lexical baselines

Thử nghiệm các mô hình lexical như TF-IDF/BM25 kết hợp TruncatedSVD và K-Means. Đây là baseline để so sánh với hướng semantic.

### Notebook 4: MiniLM ablation study

Tạo sentence embedding bằng MiniLM, giảm chiều bằng UMAP và gom cụm bằng K-Means. Kết quả cho thấy mô hình semantic cho chất lượng gom cụm tốt hơn baseline lexical.

### Notebook 5: MiniLM + FP-Max controlled hybrid

Sử dụng mô hình semantic tốt nhất, kết hợp FP-Max để khai thác mẫu phổ biến trong từng cụm, hỗ trợ đặt tên và diễn giải cụm.

### Notebook 6: Final comparison & statistical analysis

So sánh mô hình lexical và semantic qua nhiều lần chạy, đánh giá bằng các chỉ số ARI, NMI, Purity, Silhouette, Davies-Bouldin Index và Calinski-Harabasz Index, đồng thời thực hiện kiểm định thống kê.

## 5. Kết quả chính

Mô hình tốt nhất trong đồ án là:

```text
MiniLM sentence embedding + UMAP(50) + K-Means(k=6)
```

Mô hình semantic đạt kết quả tốt hơn baseline lexical trên các chỉ số đánh giá chính, đặc biệt là ARI, NMI, Purity và Silhouette. FP-Max được sử dụng sau bước gom cụm để hỗ trợ diễn giải nội dung từng cụm.

