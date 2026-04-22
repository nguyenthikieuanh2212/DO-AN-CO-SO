PIPELINE NGHIÊN CỨU CHO ĐỒ ÁN GOM CỤM VĂN BẢN BÁO CHÍ TIẾNG VIỆT

1. Mục tiêu nghiên cứu

Mục tiêu của đồ án là xây dựng một quy trình thực nghiệm hoàn chỉnh cho bài toán gom cụm văn bản báo chí tiếng Việt, trong đó dữ liệu được xử lý từ mức thô đến mức có thể phân tích ngữ nghĩa, sau đó được biểu diễn theo hai hướng tiếp cận khác nhau là lexical và semantic, trước khi tiến hành gom cụm, đánh giá, khai thác mẫu và kiểm định thống kê. Quy trình này không chỉ nhằm tạo ra các cụm có chất lượng tốt về mặt chỉ số, mà còn hướng tới khả năng diễn giải cụm một cách rõ ràng và có cơ sở học thuật.

2. Ý tưởng phương pháp luận

Toàn bộ nghiên cứu được triển khai theo hai tầng phương pháp chính.

Thứ nhất, ở tầng mô hình hóa, văn bản được biểu diễn theo hai hướng: hướng lexical dựa trên trọng số từ như TF-IDF và BM25, và hướng semantic dựa trên embedding ngữ nghĩa. Sau khi biểu diễn, dữ liệu được giảm chiều và đưa vào thuật toán gom cụm để đánh giá chất lượng bằng các chỉ số có giám sát và không giám sát.

Thứ hai, ở tầng diễn giải, sau khi mô hình tốt nhất được chọn, nghiên cứu tiếp tục khai thác mẫu phổ biến trong từng cụm bằng FP-Max, xác định chuyên mục gốc chiếm ưu thế, lựa chọn văn bản đại diện và thực hiện kiểm định thống kê nhằm chứng minh rằng sự vượt trội của mô hình tốt nhất không phải là kết quả ngẫu nhiên. Cách tiếp cận này phù hợp với định hướng “gom cụm trước, khai thác mẫu sau” đã được nhấn mạnh trong các bản mô tả pipeline trước đó. 

3. Cấu trúc 5 notebook đã thực hiện

3.1. Notebook 1 – Gộp dữ liệu và làm sạch dữ liệu đầu vào

Notebook 1 có nhiệm vụ tạo ra bộ dữ liệu chính dùng cho toàn bộ đồ án. Sáu file dữ liệu thuộc sáu chuyên mục báo chí được gộp lại thành một bảng thống nhất. Sau đó, dữ liệu được kiểm tra nhanh về missing values, URL trùng, bản ghi trùng theo cặp tiêu đề và nội dung, đồng thời tạo văn bản tổng hợp từ title, description và content. Ở bước này, nghiên cứu cũng thực hiện chuẩn hóa văn bản ở mức cơ bản, thống kê độ dài văn bản và loại bỏ các bài quá ngắn hoặc trùng lặp. Kết quả đầu ra của notebook này là file dữ liệu sạch đóng vai trò đầu vào chuẩn cho các bước NLP tiếp theo. Cách tổ chức này phù hợp với logic “gộp dữ liệu thành một file chính rồi mới tiền xử lý chi tiết”. 

3.2. Notebook 2 – Tiền xử lý tiếng Việt và xây dựng văn bản đầu vào

Notebook 2 tập trung vào xử lý ngôn ngữ tự nhiên cho tiếng Việt. Từ file dữ liệu sạch ở Notebook 1, nghiên cứu tạo cột cluster_text bằng cách ghép title, description và content. Sau đó, văn bản được chuẩn hóa để tạo cluster_text_clean, tách từ tiếng Việt để tạo cluster_text_segmented, rồi tiếp tục loại stopwords và token nhiễu nhằm xây dựng cluster_text_lexical cho nhánh lexical. Từ đây, hai cột đầu vào chính được chốt: cluster_text_lexical dùng cho nhánh lexical và cluster_text_clean dùng cho nhánh semantic. Đây là bước rất quan trọng vì nó tạo nền tảng biểu diễn đặc trưng cho các notebook sau. Trong dữ liệu đầu ra của Notebook 2, các cột cluster_text, cluster_text_clean, cluster_text_segmented và cluster_text_lexical đều đã được hình thành đầy đủ. 

3.3. Notebook 3 – Nhánh lexical: TF-IDF/BM25 + SVD + K-Means

Notebook 3 được xây dựng như một baseline theo hướng lexical. Tại đây, văn bản được biểu diễn bằng TF-IDF và BM25, sau đó giảm chiều bằng TruncatedSVD và gom cụm bằng K-Means. Nghiên cứu khảo sát nhiều giá trị k và đánh giá chất lượng bằng các chỉ số ARI, NMI, Purity, Silhouette, Davies-Bouldin Index và Calinski-Harabasz Index. Kết quả thực nghiệm cho thấy baseline tốt nhất trong nhánh lexical là BM25 + SVD(300) + K-Means(k=6). Tuy nhiên, mặc dù baseline này cho mức ARI và NMI chấp nhận được, các chỉ số nội tại như Silhouette vẫn khá thấp, cho thấy hướng lexical chưa đủ mạnh để mô hình hóa tốt cấu trúc ngữ nghĩa phức tạp của dữ liệu báo chí tiếng Việt. Kết quả này cũng phù hợp với nhận định trong các bản mô tả cũ rằng dữ liệu văn bản thực tế rất khó đạt Silhouette cực cao chỉ bằng các kỹ thuật lexical truyền thống. 

3.4. Notebook 4 – Nhánh semantic: sentence embedding + UMAP + K-Means

Notebook 4 là notebook quan trọng nhất trong giai đoạn lựa chọn mô hình. Ở notebook này, văn bản được đưa vào mô hình sentence embedding đa ngôn ngữ để tạo semantic vector, sau đó giảm chiều bằng UMAP và gom cụm bằng K-Means. Quá trình khảo sát số cụm cho thấy tại k = 6, mô hình semantic đạt sự cân bằng tốt nhất giữa khả năng tách cụm và mức độ khớp với chuyên mục gốc. Cụ thể, mô hình Semantic Embedding + UMAP(50) + K-Means(k=6) đạt Silhouette khoảng 0.6049, ARI khoảng 0.7693, NMI khoảng 0.7247, Purity khoảng 0.8918 và Davies-Bouldin Index khoảng 0.5549. Các kết quả này vượt rõ rệt so với baseline lexical. Ngoài ra, Notebook 4 còn bao gồm heatmap giữa category_clean và cụm dự đoán, biểu đồ UMAP 2D và bảng so sánh trực tiếp giữa nhánh lexical và semantic. Đây là cơ sở để chọn mô hình semantic làm mô hình tốt nhất cho toàn bộ nghiên cứu. 

3.5. Notebook 5 – Khai thác mẫu, phân tích cụm và kiểm định thống kê

Notebook 5 hoàn thiện tầng phân tích sau mô hình. Trước hết, notebook này tái thiết lập hoặc sử dụng lại kết quả của mô hình semantic tốt nhất để gắn nhãn cụm semantic cho toàn bộ dữ liệu. Sau đó, từ cluster_text_lexical, dữ liệu được chuyển sang dạng transaction để khai thác mẫu bằng FP-Max. Các mẫu phổ biến tối đại trong từng cụm được trích xuất nhằm hỗ trợ việc đặt tên cụm và nhận diện đặc trưng nội dung.

Bên cạnh FP-Max, Notebook 5 còn lấy văn bản đại diện cho từng cụm bằng cách đo độ gần centroid trong không gian semantic. Kết quả cho thấy các cụm thể thao, du lịch, sức khỏe và giáo dục có tính đồng nhất khá cao; cụm công nghệ cũng thể hiện rõ đặc trưng công nghệ và an ninh mạng; trong khi cụm xe là cụm còn giao thoa nhiều hơn, chủ yếu liên quan đến giao thông và phương tiện. Các văn bản đại diện cho từng cụm phù hợp với nhãn gốc chủ đạo và củng cố khả năng diễn giải của mô hình semantic. 

Cuối cùng, Notebook 5 thực hiện kiểm định thống kê giữa baseline lexical tốt nhất và mô hình semantic tốt nhất. Nghiên cứu tái tạo baseline BM25 + SVD(300) + K-Means(k=6), sau đó chạy lặp 10 lần với 10 seed khác nhau cho cả hai hướng tiếp cận. Các chỉ số ARI, NMI, Silhouette, Purity, Calinski-Harabasz và Davies-Bouldin được ghi lại qua từng lần chạy và so sánh bằng kiểm định Wilcoxon signed-rank test. Kết quả cho thấy mô hình semantic vượt trội baseline lexical trên toàn bộ các chỉ số chính với p-value nhỏ hơn 0.05 trong tất cả các phép kiểm định. Điều này cho phép kết luận rằng sự vượt trội của mô hình semantic là có ý nghĩa thống kê, chứ không chỉ xuất hiện ở một lần chạy ngẫu nhiên. 

4. Hai hướng biểu diễn đặc trưng đã được triển khai

Nhánh lexical sử dụng cluster_text_lexical làm đầu vào, sau đó biểu diễn văn bản bằng TF-IDF hoặc BM25. Trong các thử nghiệm lexical, BM25 kết hợp TruncatedSVD và K-Means là cấu hình mạnh nhất.

Nhánh semantic sử dụng cluster_text_clean làm đầu vào, sau đó tạo sentence embedding đa ngôn ngữ, giảm chiều bằng UMAP và gom cụm bằng K-Means. Đây là nhánh cho kết quả tốt nhất toàn bộ nghiên cứu.

Sự phân tách rõ ràng giữa lexical và semantic là điểm cốt lõi của pipeline hiện tại. Các tài liệu pipeline cũ từng đề xuất thêm HDBSCAN hoặc các cấu hình semantic khác, nhưng trong quá trình thực hiện thực tế, mô hình được chốt cuối cùng là Semantic Embedding + UMAP(50) + K-Means(k=6), vì đây là cấu hình cho kết quả định lượng và khả năng diễn giải tốt nhất. 

5. Hệ thống chỉ số đánh giá

Nghiên cứu sử dụng đồng thời hai nhóm chỉ số.

Nhóm chỉ số có giám sát gồm ARI, NMI và Purity, trong đó category_clean được dùng như ground truth ngoài để đánh giá mức độ khớp giữa cụm dự đoán và chuyên mục gốc.

Nhóm chỉ số không giám sát gồm Silhouette, Davies-Bouldin Index và Calinski-Harabasz Index. Các chỉ số này phản ánh cấu trúc nội tại của cụm, mức độ tách biệt giữa các cụm và độ chặt của từng cụm.

Việc sử dụng đồng thời hai nhóm chỉ số là cần thiết, bởi với dữ liệu báo chí tiếng Việt có sự giao thoa chủ đề, không thể chỉ nhìn vào một chỉ số đơn lẻ để kết luận. Đây cũng là cách hiểu chỉ số an toàn và học thuật hơn so với việc áp một ngưỡng cứng cho Silhouette. 

6. Vai trò của FP-Max trong đồ án

FP-Max không phải là thuật toán gom cụm chính. Trong nghiên cứu này, FP-Max được dùng sau khi đã có nhãn cụm nhằm khai thác các mẫu từ phổ biến tối đại trong từng cụm. Vai trò của FP-Max là hỗ trợ diễn giải cụm, tăng khả năng nhận diện các chủ đề con và bổ sung bằng chứng cho phần phân tích cụm. Nói cách khác, FP-Max là công cụ khai thác mẫu sau gom cụm, không thay thế cho quy trình biểu diễn và phân cụm chính. Cách hiểu này cũng phù hợp với định hướng “khai thác mẫu sau khi metric đủ ổn” đã được nêu trong các ghi chú phương pháp trước đó. 

