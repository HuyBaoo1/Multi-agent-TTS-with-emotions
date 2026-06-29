# Emotion Ground Truth Report

Reviewed valid ground-truth files used: 4

## Metrics

| provider | model | ground_truth_files | exact_match_rate | any_overlap_rate | precision | recall | f1 | predicted_emotion_coverage | error_rate_on_gt_files | tp | fp | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemini | gemini-3.5-flash | 4 | 0.25 | 0.25 | 0.3333 | 0.25 | 0.2857 | 0.75 | 0.25 | 1 | 2 | 3 |
| gemini | gemini-3.1-pro-preview | 4 | 0.0 | 0.25 | 0.25 | 0.25 | 0.25 | 0.75 | 0.25 | 1 | 3 | 3 |
| elevenlabs | scribe_v2 | 4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 4 |
| openai | gpt-4o-mini-transcribe | 4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0 | 0 | 4 |

## Annotation Issues

| file | file_id | issue | message |
| --- | --- | --- | --- |
| ground_truth\by_audio\Ice_cream_in_India_is_so_strange_you_have_to_beat_it_with_a_hammer_to_eat_it._In_824ae29722e6.csv | Ice_cream_in_India_is_so_strange_you_have_to_beat_it_with_a_hammer_to_eat_it._In_824ae29722e6 | invalid_json | Expecting ',' delimiter: line 1 column 22 (char 21) |
| ground_truth\by_audio\T_i_sao___jennyhuynh__gi_u_vi_c_l_m_content__-_vietcetera_podcast_genz_genztruye_acce78579516.csv | T_i_sao___jennyhuynh__gi_u_vi_c_l_m_content__-_vietcetera_podcast_genz_genztruye_acce78579516 | invalid_label | Invalid emotion labels: confused |

## Per-File Details

| file_id | provider | model | status | ground_truth_labels | predicted_labels | exact_match | any_overlap | tp | fp | fn | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H_m_nay_chia_s_nhanh_m_t_c_u_n_i_v_vi_c_h_c_c_a_B_c_H_48eebb92fb2d | elevenlabs | scribe_v2 | success | excited |  | False | False | 0 | 0 | 1 |  |
| H_m_nay_chia_s_nhanh_m_t_c_u_n_i_v_vi_c_h_c_c_a_B_c_H_48eebb92fb2d | gemini | gemini-3.1-pro-preview | success | excited | calm | False | False | 0 | 1 | 1 |  |
| H_m_nay_chia_s_nhanh_m_t_c_u_n_i_v_vi_c_h_c_c_a_B_c_H_48eebb92fb2d | gemini | gemini-3.5-flash | success | excited | calm | False | False | 0 | 1 | 1 |  |
| H_m_nay_chia_s_nhanh_m_t_c_u_n_i_v_vi_c_h_c_c_a_B_c_H_48eebb92fb2d | openai | gpt-4o-mini-transcribe | error | excited |  | False | False | 0 | 0 | 1 | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | elevenlabs | scribe_v2 | success | calm |  | False | False | 0 | 0 | 1 |  |
| Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | gemini | gemini-3.1-pro-preview | error | calm |  | False | False | 0 | 0 | 1 | Gemini did not return parseable JSON |
| Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | gemini | gemini-3.5-flash | error | calm |  | False | False | 0 | 0 | 1 | Gemini did not return parseable JSON |
| Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | openai | gpt-4o-mini-transcribe | error | calm |  | False | False | 0 | 0 | 1 | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| T_nh_y_u_c_th_t_s_quan_tr_ng_hay_kh_ng___To_To_postcard_t_nhy_u_tamtrang_podcast_c7147cdf2d2a | elevenlabs | scribe_v2 | success | calm |  | False | False | 0 | 0 | 1 |  |
| T_nh_y_u_c_th_t_s_quan_tr_ng_hay_kh_ng___To_To_postcard_t_nhy_u_tamtrang_podcast_c7147cdf2d2a | gemini | gemini-3.1-pro-preview | success | calm | calm;neutral | False | True | 1 | 1 | 0 |  |
| T_nh_y_u_c_th_t_s_quan_tr_ng_hay_kh_ng___To_To_postcard_t_nhy_u_tamtrang_podcast_c7147cdf2d2a | gemini | gemini-3.5-flash | success | calm | calm | True | True | 1 | 0 | 0 |  |
| T_nh_y_u_c_th_t_s_quan_tr_ng_hay_kh_ng___To_To_postcard_t_nhy_u_tamtrang_podcast_c7147cdf2d2a | openai | gpt-4o-mini-transcribe | error | calm |  | False | False | 0 | 0 | 1 | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| Tran_Thanh_is_crazy_about_the_boy_Marcus_Pham_because_of_his_adorable_speaking_t_0eb26e6b6fa3 | elevenlabs | scribe_v2 | success | excited |  | False | False | 0 | 0 | 1 |  |
| Tran_Thanh_is_crazy_about_the_boy_Marcus_Pham_because_of_his_adorable_speaking_t_0eb26e6b6fa3 | gemini | gemini-3.1-pro-preview | success | excited | happy | False | False | 0 | 1 | 1 |  |
| Tran_Thanh_is_crazy_about_the_boy_Marcus_Pham_because_of_his_adorable_speaking_t_0eb26e6b6fa3 | gemini | gemini-3.5-flash | success | excited | happy | False | False | 0 | 1 | 1 |  |
| Tran_Thanh_is_crazy_about_the_boy_Marcus_Pham_because_of_his_adorable_speaking_t_0eb26e6b6fa3 | openai | gpt-4o-mini-transcribe | error | excited |  | False | False | 0 | 0 | 1 | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
