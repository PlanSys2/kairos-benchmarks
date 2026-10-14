(define (problem drill-5) (:domain drill) (:objects h1 h2 h3 h4 h5 - hole)
(:init (bit_free) (= (rate) 1.5) (planned h1) (= (depth h1) 0) (= (min_depth h1) 12) (= (max_depth h1) 15) (planned h2) (= (depth h2) 0) (= (min_depth h2) 17) (= (max_depth h2) 20) (planned h3) (= (depth h3) 0) (= (min_depth h3) 22) (= (max_depth h3) 25) (planned h4) (= (depth h4) 0) (= (min_depth h4) 27) (= (max_depth h4) 30) (planned h5) (= (depth h5) 0) (= (min_depth h5) 32) (= (max_depth h5) 35))
(:goal (and (drilled h1) (drilled h2) (drilled h3) (drilled h4) (drilled h5))))
