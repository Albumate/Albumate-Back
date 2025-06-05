# Albumate-Back

앨범메이트 백엔드 


---
### Flask 코드 컨벤션

| 구분          | 규칙/예시                          |
| ------------- | ---------------------------------- |
| 클래스 이름   | PascalCase (`class UserModel:`)    |
| 함수/변수 이름| snake_case (`def get_user():`, `user_data`) |
| 파일(모듈)    | snake_case.py (`user_service.py`)  |
| 블루프린트    | snake_case (`bp = Blueprint('user_bp', __name__)`) |
| 템플릿 파일   | snake_case.html (`user_profile.html`) |
| 환경 변수     | UPPER_CASE (`SECRET_KEY`, `DATABASE_URL`) |
| DB 모델       | PascalCase (`class Post(db.Model):`) |
| 테스트 파일   | test_snake_case.py (`test_user_service.py`) |
  

### 커밋 룰
---

| 태그 이름  | 설명                                                   |
| ---------- | ------------------------------------------------------ |
| feat:      | 새로운 기능을 추가할 경우                                |
| fix:       | 버그를 고친 경우                                        |
| design:    | UI(HTML/CSS 등) 디자인 변경                            |
| hotfix:    | 급하게 치명적인 버그를 고쳐야 하는 경우                  |
| style:     | 코드 포맷 변경, 린트 수정 등 코드 수정이 없는 경우       |
| comment:   | 필요한 주석 추가 및 변경                                 |
| docs:      | 문서를 수정한 경우                                      |
| test:      | 테스트 추가, 테스트 리팩토링(프로덕션 코드 변경 X)      |
| chore:     | 빌드 스크립트 업데이트, 패키지 매니저 설정 등(프로덕션 코드 변경 X) |
| rename:    | 파일 혹은 폴더명을 수정하거나 옮기는 작업만인 경우       |
| remove:    | 파일을 삭제하는 작업만 수행한 경우                       |
| setting:   | 설정 파일(예: Gradle, Manifest 등)에 세팅을 추가하는 경우 |

#### 예시
예시) 

```python
- feat: 회원가입 기능 추가
- docs: Readme 수정
```
