#include <sasl/sasl.h>

int my_log(void *context, int level, const char *message)
{
    return 0;
}

int main() {
    sasl_callback_t callbacks[] = {
      {SASL_CB_LOG, (int (*)(void))&my_log, NULL },
      {SASL_CB_LIST_END, NULL, NULL },
    };

    int result;

    /* attempt to start sasl
    * See the section on Callbacks and Interactions for an
    * explanation of the variable callbacks
    */

    result=sasl_client_init(callbacks);

    /* check to see if that worked */
    return (result!=SASL_OK);
}
